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

        loop = asyncio.get_running_loop()
        self._cap = await loop.run_in_executor(None, self._open_camera)
        logger.info("Camera opened")

    @staticmethod
    def _open_camera() -> cv2.VideoCapture:
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
        if not cap.isOpened():
            raise RuntimeError("Failed to open camera")
        return cap

    def _read_and_convert(self) -> rtc.VideoFrame | None:
        """Read a frame from the camera and convert to RGBA. Runs in executor."""
        ret, frame = self._cap.read()
        if not ret:
            return None
        frame = cv2.flip(frame, -1)
        rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        return rtc.VideoFrame(WIDTH, HEIGHT, rtc.VideoBufferType.RGBA, rgba.tobytes())

    async def run(self):
        """Capture frames from camera and publish to LiveKit."""
        loop = asyncio.get_running_loop()
        while True:
            video_frame = await loop.run_in_executor(None, self._read_and_convert)
            if video_frame is None:
                await asyncio.sleep(0.01)
                continue
            self._source.capture_frame(video_frame)

    def close(self):
        """Release camera."""
        if self._cap:
            self._cap.release()
        logger.info("Video bridge closed")
