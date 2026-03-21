"""LiveKit local bridge: publishes camera video, receives control commands, drives Pico serial."""

import asyncio
import logging
import os
from pathlib import Path

import serial
from dotenv import load_dotenv
from livekit import api, rtc

from car_protocol.serial import find_pico_port, RELEASE_ALL
from local_bridge.audio import AudioBridge
from local_bridge.control import handle_control_packet, keepalive_loop
from local_bridge.video import VideoBridge

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local-bridge")


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
    video = VideoBridge(room)

    logger.info(f"Connecting to room: {room_name}")
    await room.connect(url, token)
    logger.info("Connected to LiveKit room")

    await audio.start()
    await video.start()

    try:
        await asyncio.gather(
            video.run(),
            keepalive_loop(ser, held_buttons),
        )
    except asyncio.CancelledError:
        pass
    finally:
        ser.write(bytes([RELEASE_ALL]))
        ser.close()
        video.close()
        await audio.close()
        await room.disconnect()
        logger.info("Disconnected. Released all buttons.")
