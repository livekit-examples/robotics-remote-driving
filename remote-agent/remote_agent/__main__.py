"""Entry point for `python -m remote_agent`."""

from remote_agent.main import server
from livekit.agents import cli

if __name__ == "__main__":
    cli.run_app(server)
