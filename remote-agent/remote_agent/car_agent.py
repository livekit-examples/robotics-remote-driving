"""CarAgent: AI driver that controls the car via LiveKit data channel."""

import asyncio
import logging

from livekit.agents import Agent, get_job_context
from livekit.agents.llm import function_tool

from car_protocol import UP, DOWN, LEFT, RIGHT, SPEED, BRAKE, NAME_TO_PIN
from car_protocol.commands import press_command, release_command, release_all_command

logger = logging.getLogger("remote-agent")


class CarAgent(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions=(
                "You are an AI driver controlling a remote-controlled car via voice commands. "
                "You can see through the car's onboard camera with live video input.\n\n"
                "Available controls (press-and-hold style):\n"
                "- drive_forward / drive_backward — start moving\n"
                "- turn_left / turn_right — steer\n"
                "- speed_boost — go faster\n"
                "- brake — slow down\n"
                "- stop — release ALL controls\n"
                "- release_control — release one specific control\n"
                "- press_for_duration — press a control for a specific duration in seconds\n\n"
                "You can combine controls (e.g. drive_forward + turn_left = curve left).\n"
                "Use press_for_duration for precise maneuvers. Call it multiple times in parallel "
                "to combine timed controls (e.g. forward 2s + left 0.5s = slight left curve).\n"
                "Always describe what you see in the camera when you drive.\n"
                "Always call stop when finished driving.\n"
                "When asked to find something, drive around while describing what you see "
                "until you find it, then stop."
            ),
        )

    async def _send(self, payload: bytes, topic: str):
        room = get_job_context().room
        await room.local_participant.publish_data(payload, topic=topic)

    # ── function tools (callable by the LLM) ─────────────────────────

    @function_tool()
    async def drive_forward(self):
        """Start driving forward. The car keeps moving until you call stop."""
        await self._send(*press_command(UP))
        return "Driving forward."

    @function_tool()
    async def drive_backward(self):
        """Start driving backward. The car keeps reversing until you call stop."""
        await self._send(*press_command(DOWN))
        return "Reversing."

    @function_tool()
    async def turn_left(self):
        """Steer left. Combine with drive_forward for a left curve."""
        await self._send(*press_command(LEFT))
        return "Turning left."

    @function_tool()
    async def turn_right(self):
        """Steer right. Combine with drive_forward for a right curve."""
        await self._send(*press_command(RIGHT))
        return "Turning right."

    @function_tool()
    async def speed_boost(self):
        """Activate speed boost for faster driving."""
        await self._send(*press_command(SPEED))
        return "Speed boost on."

    @function_tool()
    async def brake(self):
        """Apply the brake to slow down."""
        await self._send(*press_command(BRAKE))
        return "Braking."

    @function_tool()
    async def stop(self):
        """Release all controls — car stops completely."""
        await self._send(*release_all_command())
        return "Stopped."

    @function_tool()
    async def release_control(self, control: str):
        """Release one control without stopping everything.

        Args:
            control: One of 'forward', 'backward', 'left', 'right', 'speed', 'brake'.
        """
        pin = NAME_TO_PIN.get(control.lower())
        if pin is None:
            return f"Unknown control '{control}'."
        await self._send(*release_command(pin))
        return f"Released {control}."

    @function_tool()
    async def press_for_duration(self, control: str, duration: float):
        """Press a control for a specific duration then release it.

        Call this multiple times in parallel to combine timed controls
        (e.g. forward 2s + left 0.5s for a slight left curve).

        Args:
            control: One of 'forward', 'backward', 'left', 'right', 'speed', 'brake'.
            duration: How long to hold the control in seconds (0.1 to 10.0).
        """
        pin = NAME_TO_PIN.get(control.lower())
        if pin is None:
            return f"Unknown control '{control}'."
        duration = max(0.1, min(duration, 10.0))
        await self._send(*press_command(pin))
        await asyncio.sleep(duration)
        await self._send(*release_command(pin))
        return f"Pressed {control} for {duration}s."
