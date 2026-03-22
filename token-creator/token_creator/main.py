"""Generate a LiveKit access token and optionally dispatch an agent."""

import os
from pathlib import Path

from dotenv import load_dotenv
from livekit import api

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")


async def main(
    identity: str = "operator",
    agent_name: str | None = None,
    room_override: str | None = None,
):
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    room_name = room_override or os.environ.get("LIVEKIT_ROOM", "pico-driving")

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    print(f"URL:      {url}")
    print(f"Room:     {room_name}")
    print(f"Identity: {identity}")
    print(f"Token:    {token}")

    if agent_name:
        lkapi = api.LiveKitAPI()
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(agent_name=agent_name, room=room_name)
        )
        await lkapi.aclose()
        print(f"Agent:    {agent_name} (dispatched)")
