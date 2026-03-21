"""Pygame rendering for the Pico controller status display."""

import pygame

from car_protocol import UP, DOWN, LEFT, RIGHT, SPEED, BRAKE, BUTTON_NAMES


def draw_status(
    screen: pygame.Surface,
    font: pygame.font.Font,
    held: set[int],
    key_labels: dict[int, str],
):
    """Draw button status and key hints."""
    screen.fill((30, 30, 30))

    title = font.render("Pico Remote", True, (255, 255, 255))
    screen.blit(title, (110, 10))

    y = 50
    for btn_id in [UP, DOWN, LEFT, RIGHT, SPEED, BRAKE]:
        active = btn_id in held
        color = (0, 255, 100) if active else (100, 100, 100)
        key = key_labels[btn_id]
        name = BUTTON_NAMES[btn_id]
        label = f"[{key:>5}]  {name:<6} {'HELD' if active else ''}"
        text = font.render(label, True, color)
        screen.blit(text, (60, y))
        y += 32

    hint = font.render("WASD Tab Space | Esc=quit", True, (150, 150, 150))
    screen.blit(hint, (30, y + 15))
