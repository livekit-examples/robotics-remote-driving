#!/usr/bin/env python3
"""LiveKit local bridge: publishes camera video, receives control commands, drives Pico serial."""

import asyncio
import glob
import json
import logging
import os
import sys

import cv2
import numpy as np
import serial
from dotenv import load_dotenv
from livekit import api, rtc

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env.local"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local-bridge")

# Button pin IDs (must match Remote.h enum)
UP, DOWN, LEFT, RIGHT, SPEED, BRAKE = 16, 17, 18, 19, 20, 21
VALID_BUTTONS = {UP, DOWN, LEFT, RIGHT, SPEED, BRAKE}
RELEASE_ALL = 0x00

WIDTH, HEIGHT, FPS = 1280, 720, 30
KEEPALIVE_INTERVAL = 0.3  # must be < 500ms Pico watchdog

BUTTON_NAMES = {
    UP: "UP", DOWN: "DOWN", LEFT: "LEFT",
    RIGHT: "RIGHT", SPEED: "SPEED", BRAKE: "BRAKE",
}


def encode_press(pin: int) -> bytes:
    return bytes([pin & 0x7F])


def encode_release(pin: int) -> bytes:
    return bytes([0x80 | (pin & 0x7F)])


def find_pico_port() -> str:
    """Auto-detect Pico serial port."""
    patterns = ["/dev/tty.usbmodem*", "/dev/ttyACM*"]
    for pattern in patterns:
        ports = glob.glob(pattern)
        if ports:
            return ports[0]
    print("ERROR: No Pico found. Is it plugged in?")
    sys.exit(1)


async def main():
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    room_name = os.environ.get("LIVEKIT_ROOM", "pico-driving")
    serial_port = os.environ.get("SERIAL_PORT") or find_pico_port()

    # Open serial to Pico
    ser = serial.Serial(serial_port, 115200, timeout=0)
    logger.info(f"Serial connected: {serial_port}")

    held_buttons: set[int] = set()

    # Generate token
    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity("local-bridge")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    room = rtc.Room()

    # Handle control commands from data channel
    @room.on("data_received")
    def on_data_received(packet: rtc.DataPacket):
        if packet.topic != "control":
            return
        try:
            cmd = json.loads(packet.data.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            return

        action = cmd.get("action")
        if action == "release_all":
            ser.write(bytes([RELEASE_ALL]))
            held_buttons.clear()
            logger.info("Release all")
        elif action == "press":
            btn = cmd.get("button")
            if btn in VALID_BUTTONS:
                ser.write(encode_press(btn))
                held_buttons.add(btn)
                logger.debug(f"Press {BUTTON_NAMES.get(btn, btn)}")
        elif action == "release":
            btn = cmd.get("button")
            if btn in VALID_BUTTONS:
                ser.write(encode_release(btn))
                held_buttons.discard(btn)
                logger.debug(f"Release {BUTTON_NAMES.get(btn, btn)}")

    # Connect to LiveKit room
    logger.info(f"Connecting to room: {room_name}")
    await room.connect(url, token)
    logger.info("Connected to LiveKit room")

    # Setup video source and publish camera track
    source = rtc.VideoSource(WIDTH, HEIGHT)
    track = rtc.LocalVideoTrack.create_video_track("camera", source)
    options = rtc.TrackPublishOptions(
        source=rtc.TrackSource.SOURCE_CAMERA,
        video_encoding=rtc.VideoEncoding(max_framerate=FPS, max_bitrate=2_000_000),
    )
    await room.local_participant.publish_track(track, options)
    logger.info("Publishing camera track")

    # Open camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    if not cap.isOpened():
        logger.error("Failed to open camera")
        return

    async def capture_loop():
        """Capture frames from camera and publish to LiveKit."""
        while True:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.01)
                continue
            frame = cv2.flip(frame, -1)
            rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            video_frame = rtc.VideoFrame(
                WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, rgba.tobytes()
            )
            source.capture_frame(video_frame)
            await asyncio.sleep(1.0 / FPS)

    async def keepalive_loop():
        """Re-send held button presses to prevent Pico 500ms watchdog release."""
        while True:
            await asyncio.sleep(KEEPALIVE_INTERVAL)
            for btn in list(held_buttons):
                ser.write(encode_press(btn))

    try:
        await asyncio.gather(capture_loop(), keepalive_loop())
    except asyncio.CancelledError:
        pass
    finally:
        ser.write(bytes([RELEASE_ALL]))
        ser.close()
        cap.release()
        await room.disconnect()
        logger.info("Disconnected. Released all buttons.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
