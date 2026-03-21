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
from livekit.plugins import silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

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
        stt="deepgram/nova-3",
        llm="openai/gpt-4.1-mini",
        tts="cartesia/sonic-3",
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
    )

    await session.start(
        room=ctx.room,
        agent=CarAgent(),
    )
    await ctx.connect()
    await session.generate_reply()


if __name__ == "__main__":
    cli.run_app(server)
