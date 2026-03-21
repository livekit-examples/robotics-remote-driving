"""Control command handling: LiveKit data channel -> serial writes."""

import asyncio
import logging

import serial as pyserial

from car_protocol import ALL_BUTTONS, BUTTON_NAMES, RELEASE_ALL
from car_protocol.serial import encode_press, encode_release
from car_protocol.commands import parse_command

logger = logging.getLogger("local-bridge")


def handle_control_packet(
    data: bytes,
    ser: pyserial.Serial,
    held_buttons: set[int],
):
    """Process a control data packet from LiveKit and write to serial."""
    cmd = parse_command(data)
    if cmd is None:
        return

    action = cmd.get("action")
    if action == "release_all":
        ser.write(bytes([RELEASE_ALL]))
        held_buttons.clear()
        logger.info("Release all")
    elif action == "press":
        btn = cmd.get("button")
        if btn in ALL_BUTTONS:
            ser.write(encode_press(btn))
            held_buttons.add(btn)
            logger.debug(f"Press {BUTTON_NAMES.get(btn, btn)}")
    elif action == "release":
        btn = cmd.get("button")
        if btn in ALL_BUTTONS:
            ser.write(encode_release(btn))
            held_buttons.discard(btn)
            logger.debug(f"Release {BUTTON_NAMES.get(btn, btn)}")


async def keepalive_loop(
    ser: pyserial.Serial,
    held_buttons: set[int],
    interval: float = 0.3,
):
    """Re-send held button presses to prevent Pico 500ms watchdog release."""
    while True:
        await asyncio.sleep(interval)
        for btn in list(held_buttons):
            ser.write(encode_press(btn))
