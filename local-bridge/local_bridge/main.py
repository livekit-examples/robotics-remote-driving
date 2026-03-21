"""LiveKit local bridge: publishes camera video, receives control commands, drives Pico serial."""

import asyncio
import logging
import os
from pathlib import Path

import cv2
import serial
from dotenv import load_dotenv
from livekit import api, rtc

from car_protocol.serial import find_pico_port, RELEASE_ALL
from local_bridge.audio import AudioBridge
from local_bridge.camera import capture_loop
from local_bridge.control import handle_control_packet, keepalive_loop

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local-bridge")

WIDTH, HEIGHT, FPS = 1280, 720, 30


async def main():
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    room_name = os.environ.get("LIVEKIT_ROOM", "pico-driving")
    serial_port = os.environ.get("SERIAL_PORT") or find_pico_port()

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

    @room.on("data_received")
    def on_data_received(packet: rtc.DataPacket):
        if packet.topic != "control":
            return
        handle_control_packet(packet.data, ser, held_buttons)

    audio = AudioBridge(room)

    logger.info(f"Connecting to room: {room_name}")
    await room.connect(url, token)
    logger.info("Connected to LiveKit room")

    # Start audio bridge (mic + speaker)
    await audio.start()

    # Setup video source and publish camera track
    source = rtc.VideoSource(WIDTH, HEIGHT)
    track = rtc.LocalVideoTrack.create_video_track("camera", source)
    options = rtc.TrackPublishOptions(
        source=rtc.TrackSource.SOURCE_CAMERA,
        video_encoding=rtc.VideoEncoding(max_framerate=FPS, max_bitrate=2_000_000),
    )
    await room.local_participant.publish_track(track, options)
    logger.info("Publishing camera track")

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
    if not cap.isOpened():
        logger.error("Failed to open camera")
        return

    try:
        await asyncio.gather(
            capture_loop(cap, source, WIDTH, HEIGHT, FPS),
            keepalive_loop(ser, held_buttons),
        )
    except asyncio.CancelledError:
        pass
    finally:
        ser.write(bytes([RELEASE_ALL]))
        ser.close()
        cap.release()
        await audio.close()
        await room.disconnect()
        logger.info("Disconnected. Released all buttons.")
