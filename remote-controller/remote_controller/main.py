"""LiveKit remote controller: view camera stream and send keyboard commands to Pico."""

import asyncio
import logging
import os
import threading
from pathlib import Path

import numpy as np
import pygame
from dotenv import load_dotenv
from livekit import api, rtc

from car_protocol import UP, DOWN, LEFT, RIGHT, SPEED, BRAKE
from car_protocol.commands import press_command, release_command, release_all_command
from remote_controller.video import receive_video
from remote_controller.ui import draw_overlay

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("remote-controller")

WIDTH, HEIGHT = 1280, 720

# Key-to-button mapping (pygame-specific)
KEY_MAP = {
    pygame.K_w: UP,
    pygame.K_a: LEFT,
    pygame.K_s: DOWN,
    pygame.K_d: RIGHT,
    pygame.K_TAB: SPEED,
    pygame.K_SPACE: BRAKE,
}


async def send_command(room: rtc.Room, payload: bytes, topic: str):
    await room.local_participant.publish_data(payload, reliable=True, topic=topic)


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
    latest_frame: dict = {"frame": None}
    frame_lock = threading.Lock()

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info(f"Subscribed to video: {participant.identity}:{track.name}")
            asyncio.ensure_future(receive_video(track, latest_frame, frame_lock))

    @room.on("track_unsubscribed")
    def on_track_unsubscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        logger.info(f"Track unsubscribed: {participant.identity}:{track.name}")

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
                            await send_command(room, *press_command(btn))
                elif event.type == pygame.KEYUP:
                    if event.key in KEY_MAP:
                        btn = KEY_MAP[event.key]
                        if btn in held:
                            held.discard(btn)
                            await send_command(room, *release_command(btn))

            # Render video frame
            with frame_lock:
                frame = latest_frame["frame"]

            if frame is not None:
                surface = pygame.surfarray.make_surface(
                    np.transpose(frame, (1, 0, 2))
                )
                screen.blit(surface, (0, 0))
            else:
                screen.fill((30, 30, 30))
                waiting = font.render("Waiting for video...", True, (150, 150, 150))
                screen.blit(waiting, (WIDTH // 2 - 120, HEIGHT // 2))

            draw_overlay(screen, font, held)
            pygame.display.flip()
            clock.tick(60)

            await asyncio.sleep(0)
    finally:
        await send_command(room, *release_all_command())
        await room.disconnect()
        pygame.quit()
        logger.info("Disconnected. Released all buttons.")
