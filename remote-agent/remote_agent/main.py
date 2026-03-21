"""LiveKit AI agent server setup and session entrypoint."""

import logging
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
)
from livekit.plugins import openai, silero

from remote_agent.car_agent import CarAgent

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")

logger = logging.getLogger("remote-agent")
logger.setLevel(logging.INFO)

server = AgentServer()


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


server.setup_fnc = prewarm


@server.rtc_session(agent_name="remote-agent")
async def entrypoint(ctx: JobContext):
    session = AgentSession(
        llm=openai.realtime.RealtimeModel(voice="coral"),
        vad=ctx.proc.userdata["vad"],
    )

    await session.start(
        room=ctx.room,
        agent=CarAgent(),
    )
    await ctx.connect()
    await session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
