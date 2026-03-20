# Pico Remote Controller

Keyboard controller for the Pico remote over USB serial.

## Controls

| Key   | Action |
|-------|--------|
| W     | UP     |
| A     | LEFT   |
| S     | DOWN   |
| D     | RIGHT  |
| Tab   | SPEED  |
| Space | BRAKE  |
| Esc   | Quit   |

Hold a key to hold the button. Release to release.

## Usage

```
cd local-controller
uv run python controller.py
```

To specify a serial port manually:

```
uv run controller.py /dev/tty.usbmodem1234
```

## Protocol

Single-byte binary over serial at 115200 baud:

- Bit 7 = `0`: press, `1`: release
- Bits 0-6: GPIO pin number (16-21)
- `0x00`: release all buttons

The Pico auto-releases all buttons if no command is received for 500ms.
