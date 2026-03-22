"""Entry point for `remote-controller` CLI and `python -m remote_controller`."""

import asyncio

from remote_controller.main import main


def cli():
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
