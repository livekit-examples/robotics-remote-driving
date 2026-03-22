"""Entry point for `remote-agent` CLI and `python -m remote_agent`."""

from livekit.agents import cli

from remote_agent.main import server


def cli_main():
    cli.run_app(server)


if __name__ == "__main__":
    cli_main()
