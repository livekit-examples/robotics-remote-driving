# pico-driving

## Project Overview
Raspberry Pi Pico used as a signal spoof for a remote with active-low buttons.
6 wires drive 6 buttons by pulling lines low (open drain).

## Hardware
- Board: Raspberry Pi Pico (RP2040)
- Physical pins 16–27 → GP12–GP21 (pins 18 and 23 are GND, skipped)
- Pins configured as open drain: LOW = drive line low, HIGH = high-Z (released)
- Buttons are active-low: pulling a line low simulates a button press

## PlatformIO
- Framework: Arduino (earlephilhower core)
- Platform: maxgerhardt/platform-raspberrypi
- Pico SDK headers (e.g. `hardware/gpio.h`) are available
