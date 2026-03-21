"""Build control commands for the LiveKit data channel.

These return (payload_bytes, topic) tuples ready for
room.local_participant.publish_data(). No livekit dependency.
"""

import json

CONTROL_TOPIC = "control"


def press_command(pin: int) -> tuple[bytes, str]:
    return json.dumps({"action": "press", "button": pin}).encode(), CONTROL_TOPIC


def release_command(pin: int) -> tuple[bytes, str]:
    return json.dumps({"action": "release", "button": pin}).encode(), CONTROL_TOPIC


def release_all_command() -> tuple[bytes, str]:
    return json.dumps({"action": "release_all"}).encode(), CONTROL_TOPIC


def parse_command(data: bytes) -> dict | None:
    """Parse an incoming control data packet. Returns dict or None on error."""
    try:
        return json.loads(data.decode())
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
