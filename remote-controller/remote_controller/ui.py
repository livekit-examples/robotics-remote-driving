"""Pygame overlay rendering for the remote controller."""

import pygame

from car_protocol import UP, DOWN, LEFT, RIGHT, SPEED, BRAKE, BUTTON_NAMES

KEY_LABELS = {
    UP: "W", DOWN: "S", LEFT: "A",
    RIGHT: "D", SPEED: "Tab", BRAKE: "Space",
}


def draw_overlay(screen: pygame.Surface, font: pygame.font.Font, held: set[int]):
    """Draw semi-transparent button status overlay."""
    y = 10
    for btn_id in [UP, DOWN, LEFT, RIGHT, SPEED, BRAKE]:
        active = btn_id in held
        color = (0, 255, 100) if active else (150, 150, 150)
        key = KEY_LABELS[btn_id]
        name = BUTTON_NAMES[btn_id]
        label = f"[{key:>5}] {name:<6} {'HELD' if active else ''}"
        text = font.render(label, True, color)

        bg = pygame.Surface((text.get_width() + 8, text.get_height() + 4))
        bg.set_alpha(140)
        bg.fill((0, 0, 0))
        screen.blit(bg, (6, y - 2))
        screen.blit(text, (10, y))
        y += 26

    hint = font.render("WASD Tab Space | Esc=quit", True, (200, 200, 200))
    bg = pygame.Surface((hint.get_width() + 8, hint.get_height() + 4))
    bg.set_alpha(140)
    bg.fill((0, 0, 0))
    screen.blit(bg, (6, y + 4))
    screen.blit(hint, (10, y + 6))
