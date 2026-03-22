"""Entry point for `python -m token_creator`."""

import argparse
import asyncio

from token_creator.main import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate a LiveKit access token")
    parser.add_argument(
        "--identity",
        default="operator",
        help="participant identity (default: operator)",
    )
    parser.add_argument(
        "--agent",
        metavar="NAME",
        help="dispatch a named agent into the room",
    )
    parser.add_argument(
        "--room",
        metavar="NAME",
        help="override LIVEKIT_ROOM from env",
    )
    args = parser.parse_args()

    asyncio.run(main(identity=args.identity, agent_name=args.agent, room_override=args.room))
