"""Entry point for `python -m local_bridge`."""

import argparse
import asyncio

from local_bridge.main import main

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LiveKit local bridge")
    parser.add_argument("--agent", metavar="NAME", help="dispatch a named agent on connect")
    args = parser.parse_args()

    try:
        asyncio.run(main(agent_name=args.agent))
    except KeyboardInterrupt:
        pass
