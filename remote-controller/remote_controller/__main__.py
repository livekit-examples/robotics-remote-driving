"""Entry point for `python -m remote_controller`."""

import asyncio

from remote_controller.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
