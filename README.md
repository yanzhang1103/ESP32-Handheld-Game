# GameBoy - Handheld Action Game

A 90s-style electronic handheld game inspired by Bop It and Brain Warp, built with ESP32 microcontroller and CircuitPython.


## How to Play

### Game Objective
Complete 10 levels by performing the correct actions within the time limit. Each level displays a random action - execute it quickly to advance!

### Difficulty Levels
Use the rotary encoder to select difficulty before starting:
- **EASY**: 5 seconds per action
- **MEDIUM**: 3 seconds per action  
- **HARD**: 1.5 seconds per action

### Four Action Inputs
1. **PRESS** - Press the rotary encoder button
2. **SPIN** - Rotate the encoder knob (any direction)
3. **SHAKE** - Rapidly shake the device
4. **TILT** - Tilt the device and hold steady

### Scoring
- Score = Number of levels completed
- Complete all 10 levels to win!
- High scores are saved with player initials

## Hardware Components

### Required Components
- **Xiao ESP32-C3** - Main microcontroller
- **SSD1306 OLED Display** (128x64) - Game display
- **ADXL345 Accelerometer** - Motion detection
- **Rotary Encoder with Button** - Input control
- **NeoPixel LED** - Visual feedback
- **LiPo Battery** - Portable power
- **On/Off Switch** - Power control

### Pin Connections

| Component | ESP32 Pin | Notes |
|-----------|-----------|-------|
| NeoPixel | D0 | Data line |
| OLED SCL | D5 | Hardware I2C |
| OLED SDA | D4 | Hardware I2C |
| ADXL345 SCL | D2 | Software I2C |
| ADXL345 SDA | D3 | Software I2C |
| Encoder Button | D7 | Pull-up enabled |
| Encoder CLK | D8 | Pull-up enabled |
| Encoder DT | D9 | Pull-up enabled |
| Battery + | BAT | Through switch |
| Battery - | GND | Common ground |

### Circuit Diagram
![Circuit Diagram](GBC_game.kicad_sch.png)

### System Diagram
![System Diagram](System Diagram.png)

## Enclosure Design

The enclosure was designed to:
- **Designed according to 90's handheld game console
- **Securely house all electronics** with minimal movement
- **Provide easy access** to the USB-C port for programming
- **Include accessible on/off switch** on the side
- **Feature removable lid** for maintenance and battery replacement
- **Ergonomic design** for comfortable handheld gameplay

Materials used: [Describe your enclosure - 3D printed PLA, laser-cut acrylic, etc.]

Design considerations:
- Screen positioned at optimal viewing angle
- Rotary encoder easily accessible for spinning
- Adequate space for tilting/shaking without component damage

## Software Features

### Core Functionality
- **State machine architecture** for game flow management
- **Real-time input detection** with prioritized checking
- **Accelerometer calibration** on each level start
- **Motion filtering** to distinguish SHAKE vs TILT

### Detection Algorithms

**SHAKE Detection:**
- Monitors change from baseline position
- Threshold: `diff > 10`
- Requires 2 consecutive detections to avoid false positives

**TILT Detection:**
- Checks absolute tilt angle: `abs(x) > 5` or `abs(y) > 5`  
- Only triggers when NOT shaking (prevents confusion)
- Requires 4 consecutive readings for stability

### High Score System
- Stores top 3 scores in persistent flash storage
- Players enter 3-letter initials using rotary encoder
- Scores survive power cycles
- Default scores: AAA(100), BBB(50), CCC(25)

### Visual Feedback
**NeoPixel LED States:**
- Blue - Menu screen
- Yellow - Playing (waiting for input)
- Green - Correct action
- Red - Wrong action or timeout

### Display Screens
1. Animated startup logo
2. Difficulty selection menu
3. Game screen (level + action + score)
4. Result feedback (NICE! / WRONG!)
5. Game Over / You Win screen
6. Name entry screen
7. High score board

## Repository Structure

```
gameboy-project/
├── code.py              # Main game code
├── lib/                 # CircuitPython libraries
│   ├── adafruit_displayio_ssd1306.mpy
│   ├── adafruit_display_text/
│   ├── adafruit_adxl34x.mpy
│   └── neopixel.mpy
├── circuit_diagram.png  # Hardware wiring diagram
├── system_diagram.png   # System architecture diagram
└── README.md           # This file
```

## Installation & Setup

### 1. Install CircuitPython
- Download CircuitPython 9.x for ESP32-C3
- Flash to Xiao ESP32-C3 following [Adafruit guide](https://learn.adafruit.com/welcome-to-circuitpython)

### 2. Install Libraries
Copy all files from `lib/` folder to your device's `lib/` directory.

Required libraries:
- `adafruit_displayio_ssd1306`
- `adafruit_display_text`
- `adafruit_adxl34x`
- `neopixel`
- `adafruit_bus_device`

### 3. Upload Code
- Copy `code.py` to the root directory of your device
- Code will auto-run on power-up or reset

### 4. Troubleshooting

**Display not working:**
- Check I2C connections (D4/D5)
- Verify display address is 0x3C
- Try lowering I2C frequency

**Accelerometer not detected:**
- Game will still work with PRESS and SPIN only
- Check software I2C connections (D2/D3)
- Verify pull-up resistors on ADXL345 module

**Encoder not responsive:**
- Check all three pins (D7/D8/D9)
- Verify pull-up resistors are enabled in code

## Game Design Decisions

### Why These Thresholds?
After extensive testing, we found:
- SHAKE threshold of 10 provides good balance between sensitivity and false positives
- TILT angle of 5 degrees allows comfortable gameplay without accidental triggers
- Priority system (PRESS > SPIN > SHAKE > TILT) ensures most reliable inputs win

### Difficulty Progression
Time limits were chosen to create distinct difficulty tiers:
- Easy (5s): Comfortable for learning
- Medium (3s): Challenging but fair
- Hard (1.5s): Requires quick reflexes and practice

### High Score Implementation
Storing scores on-board was chosen over SD card to:
- Reduce hardware complexity
- Improve reliability (no card removal issues)
- Meet "no external memory" requirement


### Robust Input Detection
Priority-based checking ensures the most reliable input is detected first, preventing input conflicts.

### Motion Differentiation
SHAKE detection resets TILT counter, ensuring vigorous shaking never accidentally triggers TILT.


## Development Notes

**Challenges Faced:**
1. **I2C Pull-up Issues**: Resolved by adjusting I2C frequency and timeout settings
2. **SHAKE vs TILT Confusion**: Fixed with priority system and motion history tracking
3. **Encoder Sensitivity**: Tuned to trigger on single rotation increment

**Future Improvements:**
- Add sound effects with piezo buzzer
- Implement progressive speed increase within levels
- Create custom difficulty with adjustable parameters




**Author:** Yan Zhang  
**Date:** December 2025  
**Course:** TECHIN 512A
