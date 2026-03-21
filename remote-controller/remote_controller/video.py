"""Video stream receiver from LiveKit track."""

import logging
import threading

import numpy as np
from livekit import rtc

logger = logging.getLogger("remote-controller")


async def receive_video(
    track: rtc.Track,
    latest_frame: dict,
    frame_lock: threading.Lock,
):
    """Receive video frames from a LiveKit track into a shared buffer."""
    video_stream = rtc.VideoStream(track)
    try:
        async for event in video_stream:
            frame = event.frame.convert(rtc.VideoBufferType.RGB24)
            arr = np.frombuffer(frame.data, dtype=np.uint8).reshape(
                (frame.height, frame.width, 3)
            )
            with frame_lock:
                latest_frame["frame"] = arr
    except Exception:
        logger.exception("Error receiving video")
