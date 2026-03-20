#!/usr/bin/env python3
"""Keyboard controller for Pico remote over USB serial."""

import sys
import glob

import pygame
import serial

# Button pin IDs (must match Remote.h enum)
UP = 16
DOWN = 17
LEFT = 18
RIGHT = 19
SPEED = 20
BRAKE = 21

RELEASE_ALL = 0x00

# Key-to-button mapping
KEY_MAP = {
    pygame.K_w: UP,
    pygame.K_a: LEFT,
    pygame.K_s: DOWN,
    pygame.K_d: RIGHT,
    pygame.K_TAB: SPEED,
    pygame.K_SPACE: BRAKE,
}

BUTTON_NAMES = {
    UP: "UP", DOWN: "DOWN", LEFT: "LEFT",
    RIGHT: "RIGHT", SPEED: "SPEED", BRAKE: "BRAKE",
}

# Display layout: key label shown next to each button
KEY_LABELS = {
    UP: "W", DOWN: "S", LEFT: "A",
    RIGHT: "D", SPEED: "Tab", BRAKE: "Space",
}


def find_pico_port():
    """Auto-detect Pico serial port on macOS."""
    ports = glob.glob("/dev/tty.usbmodem*")
    if not ports:
        print("ERROR: No Pico found. Is it plugged in?")
        sys.exit(1)
    if len(ports) > 1:
        print(f"Multiple ports found: {ports}")
    print(f"Using: {ports[0]}")
    return ports[0]


def encode_press(button_id):
    return bytes([button_id & 0x7F])


def encode_release(button_id):
    return bytes([0x80 | (button_id & 0x7F)])


def main():
    port_path = sys.argv[1] if len(sys.argv) > 1 else find_pico_port()
    ser = serial.Serial(port_path, 115200, timeout=0)
    print(f"Connected to {port_path}")

    pygame.init()
    screen = pygame.display.set_mode((360, 280))
    pygame.display.set_caption("Pico Remote")
    font = pygame.font.SysFont("monospace", 22)
    clock = pygame.time.Clock()

    held = set()
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in KEY_MAP:
                        btn = KEY_MAP[event.key]
                        if btn not in held:
                            held.add(btn)
                            ser.write(encode_press(btn))
                elif event.type == pygame.KEYUP:
                    if event.key in KEY_MAP:
                        btn = KEY_MAP[event.key]
                        if btn in held:
                            held.discard(btn)
                            ser.write(encode_release(btn))

            # Draw
            screen.fill((30, 30, 30))

            title = font.render("Pico Remote", True, (255, 255, 255))
            screen.blit(title, (110, 10))

            y = 50
            for btn_id in [UP, DOWN, LEFT, RIGHT, SPEED, BRAKE]:
                active = btn_id in held
                color = (0, 255, 100) if active else (100, 100, 100)
                key = KEY_LABELS[btn_id]
                name = BUTTON_NAMES[btn_id]
                label = f"[{key:>5}]  {name:<6} {'HELD' if active else ''}"
                text = font.render(label, True, color)
                screen.blit(text, (60, y))
                y += 32

            hint = font.render("WASD Tab Space | Esc=quit", True, (150, 150, 150))
            screen.blit(hint, (30, y + 15))

            pygame.display.flip()
            clock.tick(60)
    finally:
        ser.write(bytes([RELEASE_ALL]))
        ser.close()
        pygame.quit()
        print("Released all buttons. Bye.")


if __name__ == "__main__":
    main()
