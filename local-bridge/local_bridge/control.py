"""Data I/O: receive control commands from LiveKit data channel and drive Pico serial."""

import asyncio
import logging

import serial as pyserial
from livekit import rtc

from car_protocol import ALL_BUTTONS, BUTTON_NAMES, RELEASE_ALL
from car_protocol.serial import encode_press, encode_release
from car_protocol.commands import parse_command

logger = logging.getLogger("local-bridge")


class DataBridge:
    """Manages data channel control commands and serial forwarding to the Pico."""

    def __init__(self, room: rtc.Room, serial_port: str):
        self._room = room
        self._ser = pyserial.Serial(serial_port, 115200, timeout=0)
        self._held: set[int] = set()
        logger.info(f"Serial connected: {serial_port}")

    async def start(self):
        """Register data channel handler."""
        @self._room.on("data_received")
        def on_data(packet: rtc.DataPacket):
            if packet.topic != "control":
                return
            cmd = parse_command(packet.data)
            if cmd is None:
                return

            action = cmd.get("action")
            if action == "release_all":
                self._ser.write(bytes([RELEASE_ALL]))
                self._held.clear()
            elif action == "press":
                btn = cmd.get("button")
                if btn in ALL_BUTTONS:
                    self._ser.write(encode_press(btn))
                    self._held.add(btn)
            elif action == "release":
                btn = cmd.get("button")
                if btn in ALL_BUTTONS:
                    self._ser.write(encode_release(btn))
                    self._held.discard(btn)

            self._log_state()

        logger.info("Data bridge started")

    def _log_state(self):
        if self._held:
            names = sorted(BUTTON_NAMES.get(b, str(b)) for b in self._held)
            logger.info(f"Buttons held: {', '.join(names)}")
        else:
            logger.info("Buttons held: (none)")

    async def run(self):
        """Re-send held button presses to prevent Pico 500ms watchdog release."""
        while True:
            await asyncio.sleep(0.3)
            for btn in list(self._held):
                self._ser.write(encode_press(btn))

    def close(self):
        """Release all buttons and close serial."""
        self._ser.write(bytes([RELEASE_ALL]))
        self._ser.close()
        logger.info("Data bridge closed")
