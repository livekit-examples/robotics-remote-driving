"""LiveKit local bridge: publishes camera video, receives control commands, drives Pico serial."""

import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from livekit import api, rtc

from car_protocol.serial import find_pico_port
from local_bridge.audio import AudioBridge
from local_bridge.control import DataBridge
from local_bridge.video import VideoBridge

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("local-bridge")


async def main(agent_name: str | None = None):
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    room_name = os.environ.get("LIVEKIT_ROOM", "pico-driving")
    serial_port = os.environ.get("SERIAL_PORT") or find_pico_port()

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity("local-bridge")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    room = rtc.Room()

    # Suppress "no callback attached" warnings for agent text streams
    def _noop_stream_handler(reader, participant_identity):
        pass
    room.register_text_stream_handler("lk.agent.events", _noop_stream_handler)
    room.register_text_stream_handler("lk.transcription", _noop_stream_handler)

    audio = AudioBridge(room)
    video = VideoBridge(room)
    data = DataBridge(room, serial_port)

    logger.info(f"Connecting to room: {room_name}")
    await room.connect(url, token)
    logger.info("Connected to LiveKit room")

    if agent_name:
        lkapi = api.LiveKitAPI()
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(agent_name=agent_name, room=room_name)
        )
        await lkapi.aclose()
        logger.info(f"Dispatched agent: {agent_name}")

    # Audio first so mic pump task is running before other bridges add event loop load
    await audio.start()
    await asyncio.gather(video.start(), data.start())

    try:
        await asyncio.gather(video.run(), data.run())
    except asyncio.CancelledError:
        pass
    finally:
        data.close()
        video.close()
        await audio.close()
        await room.disconnect()
        logger.info("Disconnected.")
