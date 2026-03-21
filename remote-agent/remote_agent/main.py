"""LiveKit AI agent server setup and session entrypoint."""

import asyncio
import logging
from pathlib import Path

from dotenv import load_dotenv
from livekit.agents import (
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    cli,
    inference,
)
from livekit.plugins import silero, xai
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
        llm=xai.responses.LLM(),
        tts=inference.TTS(
            model="elevenlabs/eleven_turbo_v2",
            voice="N2lVS1w4EtoT3dr4eOWO",
            language="en",
        ),
        vad=ctx.proc.userdata["vad"],
        turn_detection=MultilingualModel(),
    )

    agent = CarAgent()
    agent._session = session
    await session.start(
        room=ctx.room,
        agent=agent,
    )
    await ctx.connect()
    await session.generate_reply()

    asyncio.create_task(agent._vision_loop())


if __name__ == "__main__":
    cli.run_app(server)
