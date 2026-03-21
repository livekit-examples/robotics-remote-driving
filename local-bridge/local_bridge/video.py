"""Video I/O: capture from camera and publish to LiveKit room."""

import asyncio
import logging

import cv2
from livekit import rtc

logger = logging.getLogger("local-bridge")

WIDTH, HEIGHT, FPS = 1280, 720, 30


class VideoBridge:
    """Manages camera capture and video track publishing for a LiveKit room."""

    def __init__(self, room: rtc.Room):
        self._room = room
        self._cap: cv2.VideoCapture | None = None
        self._source = rtc.VideoSource(WIDTH, HEIGHT)

    async def start(self):
        """Open camera and publish video track."""
        track = rtc.LocalVideoTrack.create_video_track("camera", self._source)
        options = rtc.TrackPublishOptions(
            source=rtc.TrackSource.SOURCE_CAMERA,
            video_encoding=rtc.VideoEncoding(max_framerate=FPS, max_bitrate=2_000_000),
        )
        await self._room.local_participant.publish_track(track, options)
        logger.info("Published video track")

        self._cap = cv2.VideoCapture(0)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        if not self._cap.isOpened():
            raise RuntimeError("Failed to open camera")

    async def run(self):
        """Capture frames from camera and publish to LiveKit."""
        loop = asyncio.get_running_loop()
        cap = self._cap
        while True:
            ret, frame = await loop.run_in_executor(None, cap.read)
            if not ret:
                await asyncio.sleep(0.01)
                continue
            frame = cv2.flip(frame, -1)
            rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
            video_frame = rtc.VideoFrame(
                WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, rgba.tobytes()
            )
            self._source.capture_frame(video_frame)
            await asyncio.sleep(1.0 / FPS)

    def close(self):
        """Release camera."""
        if self._cap:
            self._cap.release()
        logger.info("Video bridge closed")
