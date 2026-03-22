"""Entry point for `remote-controller` CLI and `python -m remote_controller`."""

import argparse
import asyncio

from remote_controller.main import main


def cli():
    parser = argparse.ArgumentParser(
        description="LiveKit remote controller: view camera stream and drive with WASD"
    )
    parser.parse_args()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
