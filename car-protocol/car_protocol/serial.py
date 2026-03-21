"""Serial encoding for Pico communication and port auto-detection."""

import glob
import sys

RELEASE_ALL = 0x00


def encode_press(pin: int) -> bytes:
    return bytes([pin & 0x7F])


def encode_release(pin: int) -> bytes:
    return bytes([0x80 | (pin & 0x7F)])


def find_pico_port() -> str:
    """Auto-detect Pico serial port (macOS + Linux)."""
    for pattern in ["/dev/tty.usbmodem*", "/dev/ttyACM*"]:
        ports = glob.glob(pattern)
        if ports:
            if len(ports) > 1:
                print(f"Multiple ports found: {ports}")
            print(f"Using: {ports[0]}")
            return ports[0]
    print("ERROR: No Pico found. Is it plugged in?")
    sys.exit(1)
