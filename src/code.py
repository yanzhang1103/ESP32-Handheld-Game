import time
import board
import busio
import bitbangio
import digitalio
import neopixel
import displayio
import terminalio
import adafruit_displayio_ssd1306
from adafruit_display_text import label
from adafruit_adxl34x import ADXL345
import math
import random
import i2cdisplaybus
import os

# ========== High Score System ==========

SCORE_FILE = "highscore.txt"
DEFAULT_SCORES = [("AAA", 100), ("BBB", 50), ("CCC", 25)]

def load_highscores():
    """Load high scores from file or create default"""
    try:
        with open(SCORE_FILE, "r") as f:
            lines = f.read().strip().split("\n")
            scores = []
            for line in lines:
                if not line or "," not in line:
                    continue
                name, sc = line.split(",", 1)
                name = name.strip()[:3]
                try:
                    sc_int = int(sc)
                except:
                    sc_int = 0
                scores.append((name, sc_int))
            scores = (scores + DEFAULT_SCORES)[:3]
            return scores
    except:
        save_highscores(DEFAULT_SCORES)
        return DEFAULT_SCORES

def save_highscores(scores):
    """Save top 3 scores to file"""
    with open(SCORE_FILE, "w") as f:
        for name, sc in scores[:3]:
            safe_name = (name or "AAA")[:3]
            f.write(safe_name + "," + str(int(sc)) + "\n")

def check_new_highscore(score):
    """Check if score qualifies for high score board"""
    scores = load_highscores()
    for i, (_, sc) in enumerate(scores):
        if score > sc:
            return i
    return -1

# ========== Simple Encoder Class ==========

class SimpleEncoder:
    """Handle rotary encoder input"""
    def __init__(self, clk_pin, dt_pin):
        self.clk = digitalio.DigitalInOut(clk_pin)
        self.clk.direction = digitalio.Direction.INPUT
        self.clk.pull = digitalio.Pull.UP
        self.dt = digitalio.DigitalInOut(dt_pin)
        self.dt.direction = digitalio.Direction.INPUT
        self.dt.pull = digitalio.Pull.UP
        self._last_clk = self.clk.value
        self.position = 0

    def update(self):
        """Update encoder position"""
        current_clk = self.clk.value
        if current_clk != self._last_clk:
            if current_clk == 0:
                if self.dt.value != current_clk:
                    self.position += 1
                else:
                    self.position -= 1
            self._last_clk = current_clk

# ========== Hardware Initialization ==========

print("=== GameBoy Initializing ===")

# NeoPixel LED
pixel = neopixel.NeoPixel(board.D0, 1, brightness=0.2)

# OLED Display (Hardware I2C: D5=SCL, D4=SDA)
try:
    displayio.release_displays()
    time.sleep(0.1)
    i2c = busio.I2C(board.D5, board.D4, frequency=100000, timeout=1000000)
    time.sleep(0.1)
    display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
    display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)
    print("OLED Display: OK")
except Exception as e:
    print("OLED ERROR:", str(e))
    try:
        i2c = board.I2C()
        display_bus = i2cdisplaybus.I2CDisplayBus(i2c, device_address=0x3C)
        display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=64)
        print("OLED Display: OK (fallback)")
    except Exception as e2:
        print("OLED FAILED:", str(e2))
        raise

# ADXL345 Accelerometer (Software I2C: D2=SCL, D3=SDA)
accel = None
print("Initializing Accelerometer...")
try:
    soft_i2c = bitbangio.I2C(board.D2, board.D3, frequency=100000, timeout=1000000)
    time.sleep(0.2)
    accel = ADXL345(soft_i2c)
    print("ADXL345: OK")
except Exception as e:
    print("ADXL345 SKIPPED:", str(e))
    print("Game will run with PRESS and SPIN only")

# Rotary Encoder (SW=D7, CLK=D8, DT=D9)
encoder = SimpleEncoder(board.D8, board.D9)
button = digitalio.DigitalInOut(board.D7)
button.direction = digitalio.Direction.INPUT
button.pull = digitalio.Pull.UP

# ========== Display Functions ==========

def show_centered_text(text, scale=1, y=32):
    """Display centered text on screen"""
    g = displayio.Group()
    t = label.Label(terminalio.FONT, text=text, scale=scale, color=0xFFFFFF)
    t.anchor_point = (0.5, 0.5)
    t.anchored_position = (64, y)
    g.append(t)
    display.root_group = g

def show_game_ui(line1, line2=""):
    """Display game UI with level and action"""
    g = displayio.Group()
    L1 = label.Label(terminalio.FONT, text=line1, color=0xFFFFFF, scale=2)
    L1.anchor_point = (0.5, 0.5)
    L1.anchored_position = (64, 20)
    g.append(L1)
    if line2:
        L2 = label.Label(terminalio.FONT, text=line2, color=0xFFFFFF, scale=1)
        L2.anchor_point = (0.5, 0.5)
        L2.anchored_position = (64, 45)
        g.append(L2)
    display.root_group = g

# ========== High Score UI & Name Input ==========

def ask_initials(encoder, button):
    """Allow player to enter 3-letter name using rotary encoder"""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    idx = 0
    name = ["A", "A", "A"]
    pos = 0

    encoder.position = 0
    
    # Wait for button release
    while not button.value:
        time.sleep(0.01)
    time.sleep(0.3)
    
    # Display initial screen
    g = displayio.Group()
    title = label.Label(terminalio.FONT, text="ENTER NAME:", color=0xFFFFFF, x=10, y=5)
    g.append(title)
    n = label.Label(terminalio.FONT, text="".join(name), color=0xFFFFFF, scale=3, x=15, y=25)
    g.append(n)
    hint = label.Label(terminalio.FONT, text="Spin=ltr Press=nxt", color=0xFFFFFF, x=2, y=58)
    g.append(hint)
    display.root_group = g
    display.refresh()

    while True:
        encoder.update()
        new_idx = encoder.position % 26
        if new_idx != idx:
            idx = new_idx
            name[pos] = letters[idx]

            # Update display
            g = displayio.Group()
            title = label.Label(terminalio.FONT, text="ENTER NAME:", color=0xFFFFFF, x=10, y=5)
            g.append(title)
            n = label.Label(terminalio.FONT, text="".join(name), color=0xFFFFFF, scale=3, x=15, y=25)
            g.append(n)
            hint = label.Label(terminalio.FONT, text="Spin=ltr Press=nxt", color=0xFFFFFF, x=2, y=58)
            g.append(hint)
            display.root_group = g
            display.refresh()

        if not button.value:
            time.sleep(0.3)
            while not button.value:
                time.sleep(0.01)
            time.sleep(0.2)
            
            pos += 1
            if pos >= 3:
                return "".join(name)
            encoder.position = 0
            idx = 0
            
        time.sleep(0.01)

def show_highscores():
    """Display high score board"""
    scores = load_highscores()
    g = displayio.Group()
    title = label.Label(terminalio.FONT, text="HIGH SCORES", color=0xFFFFFF, x=20, y=8)
    g.append(title)
    y = 22
    for i, (name, sc) in enumerate(scores):
        line = label.Label(terminalio.FONT, text=str(i+1)+". "+name+"  "+str(sc), color=0xFFFFFF, x=20, y=y)
        g.append(line)
        y += 12
    bottom = label.Label(terminalio.FONT, text="Press button", color=0xFFFFFF, x=25, y=56)
    g.append(bottom)
    display.root_group = g
    display.refresh()

# ========== Startup Animation ==========

def play_startup_logo():
    """Display animated startup logo"""
    TITLE = "GameBoy"
    for s in range(1, 5):
        g = displayio.Group()
        t = label.Label(terminalio.FONT, text=TITLE, color=0xFFFFFF, scale=s)
        t.anchor_point = (0.5, 0.5)
        t.anchored_position = (64, 32)
        g.append(t)
        display.root_group = g
        display.refresh()
        time.sleep(0.2)
    time.sleep(0.5)

def play_intro_sequence():
    """Play startup sequence"""
    play_startup_logo()
    show_centered_text("Let's play!", scale=1)
    time.sleep(2.5)

# ========== Menu System ==========

menu_group = displayio.Group()
lbl_title = label.Label(terminalio.FONT, text="SELECT DIFFICULTY", color=0xFFFFFF, x=10, y=8)
lbl_easy  = label.Label(terminalio.FONT, text="EASY",   color=0xFFFFFF, x=30, y=24)
lbl_med   = label.Label(terminalio.FONT, text="MEDIUM", color=0xFFFFFF, x=30, y=40)
lbl_hard  = label.Label(terminalio.FONT, text="HARD",   color=0xFFFFFF, x=30, y=56)
cursor    = label.Label(terminalio.FONT, text="->", color=0xFFFFFF, x=5, y=24)
menu_group.append(lbl_title)
menu_group.append(lbl_easy)
menu_group.append(lbl_med)
menu_group.append(lbl_hard)
menu_group.append(cursor)

def update_menu_cursor(i):
    """Update menu cursor position"""
    cursor.y = 24 + i * 16
    display.root_group = menu_group

# ========== Game Configuration ==========

# Available moves based on hardware
if accel:
    MOVES = ["PRESS", "SPIN", "SHAKE", "TILT"]
    print("All moves available")
else:
    MOVES = ["PRESS", "SPIN"]
    print("Limited to PRESS and SPIN")

# Time limits for each difficulty
TIME_LIMITS = [5.0, 3.0, 1.5]  # Easy, Medium, Hard

# Game state variables
state = "BOOT"
level = 1
diff_index = 0
last_diff_index = -1

print("=== Ready to Play ===\n")

# ========== Main Game Loop ==========

while True:
    encoder.update()

    # ===== Boot Sequence =====
    if state == "BOOT":
        play_intro_sequence()
        state = "MENU"

    # ===== Main Menu =====
    elif state == "MENU":
        pixel.fill((0, 0, 50))  # Blue LED
        diff_index = encoder.position % 3
        if diff_index != last_diff_index:
            update_menu_cursor(diff_index)
            last_diff_index = diff_index
        if not button.value:
            time.sleep(0.2)
            state = "PLAY"
            level = 1

    # ===== Playing Game =====
    elif state == "PLAY":
        target_move = random.choice(MOVES)
        time_limit = TIME_LIMITS[diff_index]
        current_score = level - 1

        pixel.fill((50, 50, 0))  # Yellow LED
        show_game_ui("LVL "+str(level), target_move+"!  Sc:"+str(current_score))
        display.refresh()

        start = time.monotonic()
        start_pos = encoder.position
        detected_action = None
        
        # Establish accelerometer baseline
        baseline_x, baseline_y, baseline_z = 0, 0, 9.8
        if accel:
            try:
                baseline_x, baseline_y, baseline_z = accel.acceleration
                time.sleep(0.05)
            except:
                pass
        
        # Detection state variables
        shake_count = 0
        tilt_count = 0

        # Input detection loop
        while (time.monotonic() - start < time_limit) and (detected_action is None):
            encoder.update()

            # Check button press
            if not button.value:
                detected_action = "PRESS"
                break
            
            # Check encoder rotation
            encoder_delta = abs(encoder.position - start_pos)
            if encoder_delta >= 1:
                detected_action = "SPIN"
                break

            # Check accelerometer
            if accel:
                try:
                    x, y, z = accel.acceleration
                    x_diff = abs(x - baseline_x)
                    y_diff = abs(y - baseline_y)
                    z_diff = abs(z - baseline_z)
                    max_diff = max(x_diff, y_diff, z_diff)
                    
                    # SHAKE: Big rapid movement (lowered threshold)
                    if max_diff > 10:  # More sensitive (was 12)
                        shake_count += 1
                        tilt_count = 0  # Reset tilt if shaking
                        if shake_count >= 2:
                            detected_action = "SHAKE"
                            break
                    else:
                        shake_count = 0
                        
                        # TILT: Only check when NOT shaking
                        # Just check if device is tilted (lowered threshold)
                        if abs(x) > 5 or abs(y) > 5:  # More sensitive (was 6)
                            tilt_count += 1
                            if tilt_count >= 4:  # Faster trigger (was 5)
                                detected_action = "TILT"
                                break
                        else:
                            tilt_count = 0
                        
                except Exception as e:
                    pass
            
            time.sleep(0.02)

        # Evaluate result
        if detected_action == target_move:
            pixel.fill((0, 255, 0))  # Green LED
            show_centered_text("NICE!", scale=2)
            time.sleep(1)
            level += 1
            if level > 10:
                state = "WIN"
        else:
            pixel.fill((255, 0, 0))  # Red LED
            show_centered_text("WRONG!", scale=2)
            time.sleep(1)
            state = "GAMEOVER"

    # ===== Game Over =====
    elif state == "GAMEOVER":
        final_score = level - 1

        # Display game over screen
        g = displayio.Group()
        g.append(label.Label(terminalio.FONT, text="GAME OVER", color=0xFFFFFF, scale=2, x=10, y=15))
        g.append(label.Label(terminalio.FONT, text="Score: "+str(final_score), color=0xFFFFFF, scale=1, x=25, y=40))
        display.root_group = g
        display.refresh()
        time.sleep(2)

        # Check for high score
        rank = check_new_highscore(final_score)
        
        # Always ask for name
        g = displayio.Group()
        g.append(label.Label(terminalio.FONT, text="ENTER NAME", color=0xFFFFFF, scale=1, x=25, y=15))
        g.append(label.Label(terminalio.FONT, text="Score: "+str(final_score), color=0xFFFFFF, scale=1, x=25, y=30))
        g.append(label.Label(terminalio.FONT, text="Press button", color=0xFFFFFF, x=20, y=50))
        display.root_group = g
        display.refresh()
        
        # Wait for button press
        while button.value:
            time.sleep(0.01)
        time.sleep(0.3)
        while not button.value:
            time.sleep(0.01)
        time.sleep(0.3)

        # Get player name
        name = ask_initials(encoder, button)
        
        # Save if high score
        if rank >= 0:
            scores = load_highscores()
            scores.insert(rank, (name, final_score))
            save_highscores(scores[:3])

        # Show high scores
        show_highscores()
        
        # Wait for button to return to menu
        while button.value:
            time.sleep(0.01)
        time.sleep(0.2)
        while not button.value:
            time.sleep(0.01)
        time.sleep(0.2)

        level = 1
        last_diff_index = -1
        state = "MENU"

    # ===== Win Screen =====
    elif state == "WIN":
        final_score = level - 1

        # Display win screen
        g = displayio.Group()
        w1 = label.Label(terminalio.FONT, text="YOU WIN!", color=0xFFFFFF, scale=2)
        w1.anchor_point = (0.5, 0.5)
        w1.anchored_position = (64, 20)
        g.append(w1)
        w2 = label.Label(terminalio.FONT, text="Score: "+str(final_score), color=0xFFFFFF, scale=1)
        w2.anchor_point = (0.5, 0.5)
        w2.anchored_position = (64, 45)
        g.append(w2)
        display.root_group = g
        display.refresh()
        time.sleep(2)

        # Check for high score
        rank = check_new_highscore(final_score)
        
        # Always ask for name
        g = displayio.Group()
        g.append(label.Label(terminalio.FONT, text="ENTER NAME", color=0xFFFFFF, scale=1, x=25, y=15))
        g.append(label.Label(terminalio.FONT, text="Score: "+str(final_score), color=0xFFFFFF, scale=1, x=25, y=30))
        g.append(label.Label(terminalio.FONT, text="Press button", color=0xFFFFFF, x=20, y=50))
        display.root_group = g
        display.refresh()
        
        # Wait for button press
        while button.value:
            time.sleep(0.01)
        time.sleep(0.3)
        while not button.value:
            time.sleep(0.01)
        time.sleep(0.3)

        # Get player name
        name = ask_initials(encoder, button)
        
        # Save if high score
        if rank >= 0:
            scores = load_highscores()
            scores.insert(rank, (name, final_score))
            save_highscores(scores[:3])

        # Show high scores
        show_highscores()
        
        # Wait for button to return to menu
        while button.value:
            time.sleep(0.01)
        time.sleep(0.2)
        while not button.value:
            time.sleep(0.01)
        time.sleep(0.2)

        level = 1
        last_diff_index = -1
        state = "MENU"  
