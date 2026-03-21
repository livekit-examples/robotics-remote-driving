"""Entry point for `python -m local_bridge`."""

import asyncio

from local_bridge.main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
