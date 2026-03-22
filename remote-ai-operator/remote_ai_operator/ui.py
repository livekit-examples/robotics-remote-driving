"""Pygame overlay rendering for the AI operator."""

import pygame

from car_protocol import UP, DOWN, LEFT, RIGHT, SPEED, BRAKE, BUTTON_NAMES


BAR_W = 120
BAR_H = 16


def draw_overlay(
    screen: pygame.Surface,
    font: pygame.font.Font,
    held: set[int],
    paused: bool,
    step_count: int,
    inference_ms: float = 0.0,
    action_values: dict[int, float] | None = None,
    threshold: float = 0.5,
):
    """Draw semi-transparent status overlay."""
    y = 10

    # AI status badge
    if paused:
        badge_text = "AI PAUSED"
        badge_color = (255, 200, 0)
    else:
        badge_text = "AI DRIVING"
        badge_color = (0, 200, 255)

    badge = font.render(badge_text, True, badge_color)
    bg = pygame.Surface((badge.get_width() + 8, badge.get_height() + 4))
    bg.set_alpha(180)
    bg.fill((0, 0, 0))
    screen.blit(bg, (6, y - 2))
    screen.blit(badge, (10, y))
    y += 30

    # Step counter + latency
    info_text = f"Step: {step_count}  |  {inference_ms:.1f}ms"
    steps = font.render(info_text, True, (180, 180, 180))
    bg = pygame.Surface((steps.get_width() + 8, steps.get_height() + 4))
    bg.set_alpha(140)
    bg.fill((0, 0, 0))
    screen.blit(bg, (6, y - 2))
    screen.blit(steps, (10, y))
    y += 30

    # Button status with confidence bars
    for btn_id in [UP, DOWN, LEFT, RIGHT, SPEED, BRAKE]:
        conf = action_values.get(btn_id, 0.0) if action_values else 0.0
        active = btn_id in held
        name = BUTTON_NAMES[btn_id]

        # Label + value
        text_color = (0, 255, 100) if active else (150, 150, 150)
        label = font.render(f"{name:<6} {conf:+.2f}", True, text_color)

        row_w = label.get_width() + 12 + BAR_W + 8
        row_h = max(label.get_height(), BAR_H) + 4
        bg = pygame.Surface((row_w, row_h))
        bg.set_alpha(140)
        bg.fill((0, 0, 0))
        screen.blit(bg, (6, y - 2))
        screen.blit(label, (10, y))

        # Confidence bar
        bar_x = 10 + label.get_width() + 8
        bar_y = y + (label.get_height() - BAR_H) // 2

        # Bar background
        pygame.draw.rect(screen, (60, 60, 60), (bar_x, bar_y, BAR_W, BAR_H))

        # Threshold marker
        thresh_x = bar_x + int(threshold * BAR_W)
        pygame.draw.line(screen, (255, 255, 255), (thresh_x, bar_y), (thresh_x, bar_y + BAR_H), 1)

        # Fill bar (clamp 0-1)
        fill = max(0.0, min(1.0, conf))
        fill_w = int(fill * BAR_W)
        bar_color = (0, 255, 100) if active else (100, 100, 200)
        if fill_w > 0:
            pygame.draw.rect(screen, bar_color, (bar_x, bar_y, fill_w, BAR_H))

        y += 26

    # Hint
    hint = font.render("Tab=speed  Space=brake  P=pause  Esc=quit", True, (200, 200, 200))
    bg = pygame.Surface((hint.get_width() + 8, hint.get_height() + 4))
    bg.set_alpha(140)
    bg.fill((0, 0, 0))
    screen.blit(bg, (6, y + 4))
    screen.blit(hint, (10, y + 6))
