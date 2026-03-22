#!/usr/bin/env python3
"""Keyboard controller for Pico remote over USB serial."""

import argparse

import pygame
import serial

from car_protocol import UP, DOWN, LEFT, RIGHT, SPEED, BRAKE
from car_protocol.serial import encode_press, encode_release, find_pico_port, RELEASE_ALL
from local_controller.ui import draw_status

# Key-to-button mapping (pygame-specific)
KEY_MAP = {
    pygame.K_w: UP,
    pygame.K_a: LEFT,
    pygame.K_s: DOWN,
    pygame.K_d: RIGHT,
    pygame.K_TAB: SPEED,
    pygame.K_SPACE: BRAKE,
}

KEY_LABELS = {
    UP: "W", DOWN: "S", LEFT: "A",
    RIGHT: "D", SPEED: "Tab", BRAKE: "Space",
}


def main():
    parser = argparse.ArgumentParser(
        description="Direct USB serial controller for Pico driving (no LiveKit)"
    )
    parser.add_argument("port", nargs="?", default=None, help="serial port (auto-detected if omitted)")
    args = parser.parse_args()

    port_path = args.port or find_pico_port()
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

            # Re-send held presses to prevent Pico 500ms watchdog release
            for btn in held:
                ser.write(encode_press(btn))

            draw_status(screen, font, held, KEY_LABELS)
            pygame.display.flip()
            clock.tick(60)
    finally:
        ser.write(bytes([RELEASE_ALL]))
        ser.close()
        pygame.quit()
        print("Released all buttons. Bye.")


if __name__ == "__main__":
    main()
