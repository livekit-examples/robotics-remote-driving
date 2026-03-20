#!/usr/bin/env python3
"""LiveKit remote controller: view camera stream and send keyboard commands to Pico."""

import asyncio
import json
import logging
import os
import threading

import numpy as np
import pygame
from dotenv import load_dotenv
from livekit import api, rtc

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("remote-controller")

# Button pin IDs (must match Remote.h enum)
UP, DOWN, LEFT, RIGHT, SPEED, BRAKE = 16, 17, 18, 19, 20, 21

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

KEY_LABELS = {
    UP: "W", DOWN: "S", LEFT: "A",
    RIGHT: "D", SPEED: "Tab", BRAKE: "Space",
}

WIDTH, HEIGHT = 640, 480


async def main():
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    room_name = os.environ.get("LIVEKIT_ROOM", "pico-driving")

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity("controller")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    room = rtc.Room()
    latest_frame: dict = {"frame": None}  # mutable container for cross-task sharing
    frame_lock = threading.Lock()

    # Subscribe to local-bridge's camera track
    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info(f"Subscribed to video: {participant.identity}:{track.name}")
            asyncio.ensure_future(receive_video(track))

    async def receive_video(track: rtc.Track):
        video_stream = rtc.VideoStream(track)
        try:
            async for event in video_stream:
                frame = event.frame.convert(rtc.VideoBufferType.RGB24)
                arr = np.frombuffer(frame.data, dtype=np.uint8).reshape(
                    (frame.height, frame.width, 3)
                )
                with frame_lock:
                    latest_frame["frame"] = arr
        except Exception:
            logger.exception("Error receiving video")

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logger.info(f"Track unsubscribed: {participant.identity}:{track.name}")

    async def send_command(cmd: dict):
        await room.local_participant.publish_data(
            json.dumps(cmd).encode(),
            reliable=True,
            topic="control",
        )

    # Connect to room
    logger.info(f"Connecting to room: {room_name}")
    await room.connect(url, token)
    logger.info("Connected. Waiting for local-bridge video...")

    # Pygame for keyboard input and display
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pico LiveKit Controller")
    font = pygame.font.SysFont("monospace", 20)
    clock = pygame.time.Clock()

    held: set[int] = set()
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
                            await send_command({"action": "press", "button": btn})
                elif event.type == pygame.KEYUP:
                    if event.key in KEY_MAP:
                        btn = KEY_MAP[event.key]
                        if btn in held:
                            held.discard(btn)
                            await send_command({"action": "release", "button": btn})

            # Render video frame
            with frame_lock:
                frame = latest_frame["frame"]

            if frame is not None:
                # Convert RGB numpy array to pygame surface
                surface = pygame.surfarray.make_surface(
                    np.transpose(frame, (1, 0, 2))
                )
                screen.blit(surface, (0, 0))
            else:
                screen.fill((30, 30, 30))
                waiting = font.render("Waiting for video...", True, (150, 150, 150))
                screen.blit(waiting, (WIDTH // 2 - 120, HEIGHT // 2))

            # Draw control overlay
            draw_overlay(screen, font, held)

            pygame.display.flip()
            clock.tick(60)

            # Yield to asyncio event loop
            await asyncio.sleep(0)
    finally:
        await send_command({"action": "release_all"})
        await room.disconnect()
        pygame.quit()
        logger.info("Disconnected. Released all buttons.")


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

        # Dark background behind text for readability
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


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
