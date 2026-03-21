"""Camera capture loop: OpenCV -> LiveKit VideoSource."""

import asyncio
import logging

import cv2
from livekit import rtc

logger = logging.getLogger("local-bridge")


async def capture_loop(
    cap: cv2.VideoCapture,
    source: rtc.VideoSource,
    width: int,
    height: int,
    fps: int,
):
    """Capture frames from camera and publish to LiveKit."""
    while True:
        ret, frame = cap.read()
        if not ret:
            await asyncio.sleep(0.01)
            continue
        frame = cv2.flip(frame, -1)
        rgba = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        video_frame = rtc.VideoFrame(
            width, height, rtc.VideoBufferType.RGBA, rgba.tobytes()
        )
        source.capture_frame(video_frame)
        await asyncio.sleep(1.0 / fps)
