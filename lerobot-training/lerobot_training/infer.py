"""Run inference with a trained LeRobot policy over LiveKit.

Connects to a LiveKit room, receives camera frames, runs the policy,
and sends control commands back via data channel — replacing the human operator.

Usage:
    uv run lerobot-infer --checkpoint ./outputs/train/checkpoints/last/pretrained_model
    uv run lerobot-infer --checkpoint ./outputs/train/checkpoints/last/pretrained_model --room my-room
"""

import argparse
import asyncio
import json
import os
from pathlib import Path

import numpy as np
import torch
from dotenv import load_dotenv
from livekit import api, rtc
from PIL import Image

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")

# Mirrors car-protocol/buttons.py
BUTTONS = {"UP": 16, "DOWN": 17, "LEFT": 18, "RIGHT": 19, "SPEED": 20, "BRAKE": 21}
ACTION_KEYS = ["forward", "backward", "left", "right", "speed", "brake"]
ACTION_TO_BUTTON = {
    "forward": BUTTONS["UP"],
    "backward": BUTTONS["DOWN"],
    "left": BUTTONS["LEFT"],
    "right": BUTTONS["RIGHT"],
    "speed": BUTTONS["SPEED"],
    "brake": BUTTONS["BRAKE"],
}
CONTROL_TOPIC = "control"


def load_policy(checkpoint_path: str, device: str):
    """Load a trained LeRobot policy from checkpoint."""
    from lerobot.common.policies.factory import make_policy

    policy = make_policy(pretrained_name_or_path=checkpoint_path)
    policy.to(device)
    policy.eval()
    return policy


async def run_inference(
    checkpoint_path: str,
    device: str,
    fps: int,
    room_override: str | None,
    threshold: float,
):
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    room_name = room_override or os.environ.get("LIVEKIT_ROOM", "pico-driving")

    print(f"Loading policy from {checkpoint_path}...")
    policy = load_policy(checkpoint_path, device)
    print(f"Policy loaded on {device}")

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity("lerobot-inference")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    room = rtc.Room()
    latest_frame: dict = {"frame": None}
    prev_pressed: set[int] = set()

    @room.on("track_subscribed")
    def on_track(track: rtc.Track, pub, participant):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            print(f"Subscribed to video from {participant.identity}")
            asyncio.ensure_future(_receive_frames(track, latest_frame))

    print(f"Connecting to room: {room_name}")
    await room.connect(url, token)
    print("Connected. Waiting for video...")

    async def send_control(action: str, button: int | None = None):
        payload = json.dumps({"action": action, "button": button} if button else {"action": action})
        await room.local_participant.publish_data(
            payload.encode(), reliable=True, topic=CONTROL_TOPIC
        )

    interval = 1.0 / fps
    try:
        while True:
            await asyncio.sleep(interval)

            frame = latest_frame["frame"]
            if frame is None:
                continue

            # Prepare observation for policy
            img = Image.fromarray(frame).convert("RGB")
            img_tensor = torch.from_numpy(np.array(img)).permute(2, 0, 1).float() / 255.0
            img_tensor = img_tensor.unsqueeze(0).to(device)

            observation = {"observation.images.camera": img_tensor}

            with torch.no_grad():
                action = policy.select_action(observation)

            # action is [6] tensor: [forward, backward, left, right, speed, brake]
            action_np = action.squeeze().cpu().numpy()

            # Determine which buttons to press (threshold binary actions)
            pressed: set[int] = set()
            for i, key in enumerate(ACTION_KEYS):
                if action_np[i] > threshold:
                    pressed.add(ACTION_TO_BUTTON[key])

            # Send press/release delta
            for btn in pressed - prev_pressed:
                await send_control("press", btn)
            for btn in prev_pressed - pressed:
                await send_control("release", btn)

            prev_pressed.clear()
            prev_pressed.update(pressed)

    except asyncio.CancelledError:
        pass
    finally:
        await send_control("release_all")
        await room.disconnect()
        print("Disconnected. Released all buttons.")


async def _receive_frames(track: rtc.Track, latest_frame: dict):
    """Receive video frames from a LiveKit video track."""
    stream = rtc.VideoStream(track)
    async for event in stream:
        frame = event.frame
        latest_frame["frame"] = frame.convert(rtc.VideoBufferType.RGBA).data.reshape(
            frame.height, frame.width, 4
        )[:, :, :3]  # RGBA -> RGB


def cli():
    parser = argparse.ArgumentParser(
        description="Run a trained LeRobot policy over LiveKit to drive the robot"
    )
    parser.add_argument("--checkpoint", required=True, help="Path to trained policy checkpoint")
    parser.add_argument("--device", default=None, help="Device: cuda, mps, cpu (auto-detected)")
    parser.add_argument("--fps", type=int, default=10, help="Inference FPS (default: 10)")
    parser.add_argument("--room", metavar="NAME", help="Override LIVEKIT_ROOM from env")
    parser.add_argument(
        "--threshold", type=float, default=0.5,
        help="Action threshold for binary controls (default: 0.5)",
    )
    args = parser.parse_args()

    device = args.device
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    try:
        asyncio.run(run_inference(
            checkpoint_path=args.checkpoint,
            device=device,
            fps=args.fps,
            room_override=args.room,
            threshold=args.threshold,
        ))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
