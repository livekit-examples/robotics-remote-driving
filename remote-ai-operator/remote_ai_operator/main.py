"""AI-driven remote operator: receive video, run policy, send controls."""

import asyncio
import concurrent.futures
import logging
import os
import threading
import time
from pathlib import Path

import numpy as np
import pygame
import torch
from dotenv import load_dotenv
from livekit import api, rtc
from PIL import Image

from car_protocol import UP, DOWN, LEFT, RIGHT, SPEED, BRAKE
from car_protocol.commands import press_command, release_command, release_all_command
from remote_ai_operator.video import receive_video
from remote_ai_operator.ui import draw_overlay

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env.local")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("remote-ai-operator")

WIDTH, HEIGHT = 1280, 720

# Must match training resolution
FRAME_W, FRAME_H = 320, 180

ACTION_KEYS = ["forward", "backward", "left", "right", "speed", "brake"]
ACTION_TO_BUTTON = {
    "forward": UP, "backward": DOWN,
    "left": LEFT, "right": RIGHT,
    "speed": SPEED, "brake": BRAKE,
}

# Thread pool for running inference off the main loop
_inference_pool = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="inference")


def resolve_checkpoint(checkpoint_path: str) -> str:
    """Resolve local paths to absolute, pass repo IDs through."""
    path = Path(checkpoint_path)
    if path.exists():
        return str(path.resolve())
    elif "/" in checkpoint_path and not checkpoint_path.count("/") == 1:
        raise FileNotFoundError(f"Checkpoint not found: {path.resolve()}")
    return checkpoint_path


def load_policy(checkpoint_path: str, device: str):
    """Load a trained ACT policy and normalization stats from checkpoint."""
    from lerobot.policies.act.modeling_act import ACTPolicy
    import safetensors.torch as st

    checkpoint_path = resolve_checkpoint(checkpoint_path)

    logger.info(f"Loading policy from {checkpoint_path}")
    policy = ACTPolicy.from_pretrained(checkpoint_path)
    policy.to(device)
    policy.eval()

    # Load normalization stats from preprocessor
    stats_file = Path(checkpoint_path) / "policy_preprocessor_step_3_normalizer_processor.safetensors"
    stats = st.load_file(str(stats_file))

    norm_stats = {
        "image_mean": stats["observation.images.camera.mean"].to(device),  # (3,1,1)
        "image_std": stats["observation.images.camera.std"].to(device),    # (3,1,1)
        "state_mean": stats["observation.state.mean"].to(device),          # (6,)
        "state_std": stats["observation.state.std"].to(device),            # (6,)
        "action_mean": stats["action.mean"].to(device),                    # (6,)
        "action_std": stats["action.std"].to(device),                      # (6,)
    }

    logger.info(f"Policy loaded on {device}")
    return policy, norm_stats


def run_inference(frame: np.ndarray, policy, norm_stats, prev_action_raw, device):
    """Run policy inference on a frame. Called from a thread pool to avoid blocking the UI."""
    img = Image.fromarray(frame).convert("RGB").resize(
        (FRAME_W, FRAME_H), Image.LANCZOS
    )
    img_tensor = (
        torch.from_numpy(np.array(img))
        .permute(2, 0, 1)
        .float() / 255.0
    ).to(device)

    img_norm = (img_tensor - norm_stats["image_mean"]) / norm_stats["image_std"]
    state_norm = (prev_action_raw.to(device) - norm_stats["state_mean"]) / norm_stats["state_std"]

    observation = {
        "observation.images.camera": img_norm.unsqueeze(0),
        "observation.state": state_norm.unsqueeze(0),
    }

    t0 = time.perf_counter()
    with torch.no_grad():
        raw_action = policy.select_action(observation)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    action_denorm = raw_action.squeeze() * norm_stats["action_std"] + norm_stats["action_mean"]
    action_np = action_denorm.cpu().numpy()

    return action_np, elapsed_ms


async def send_command(room: rtc.Room, payload: bytes, topic: str):
    await room.local_participant.publish_data(payload, reliable=True, topic=topic)


async def main(
    checkpoint_path: str,
    device: str,
    threshold: float,
    room_override: str | None,
):
    url = os.environ["LIVEKIT_URL"]
    api_key = os.environ["LIVEKIT_API_KEY"]
    api_secret = os.environ["LIVEKIT_API_SECRET"]
    room_name = room_override or os.environ.get("LIVEKIT_ROOM", "pico-driving")

    policy, norm_stats = load_policy(checkpoint_path, device)

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity("ai-operator")
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    room = rtc.Room()
    latest_frame: dict = {"frame": None}
    frame_lock = threading.Lock()

    @room.on("track_subscribed")
    def on_track_subscribed(
        track: rtc.Track,
        publication: rtc.RemoteTrackPublication,
        participant: rtc.RemoteParticipant,
    ):
        if track.kind == rtc.TrackKind.KIND_VIDEO:
            logger.info(f"Subscribed to video: {participant.identity}:{track.name}")
            asyncio.ensure_future(receive_video(track, latest_frame, frame_lock))

    logger.info(f"Connecting to room: {room_name}")
    await room.connect(url, token)
    logger.info("Connected. Waiting for video...")

    # Pygame for display
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("AI Operator — LeRobot")
    font = pygame.font.SysFont("monospace", 20)
    clock = pygame.time.Clock()

    held: set[int] = set()
    manual_held: set[int] = set()  # Manually held buttons (speed/brake)
    press_time: dict[int, float] = {}  # When each button was last pressed (for debounce)
    DEBOUNCE_S = 0.2  # Minimum hold time before AI can release a button
    prev_action_raw = torch.zeros(len(ACTION_KEYS), dtype=torch.float32)
    paused = True
    running = True
    step_count = 0
    inference_ms = 0.0
    action_values: dict[int, float] = {ACTION_TO_BUTTON[k]: 0.0 for k in ACTION_KEYS}
    inference_future: concurrent.futures.Future | None = None
    loop = asyncio.get_event_loop()

    # Keys for manual override (speed/brake)
    MANUAL_KEY_MAP = {
        pygame.K_TAB: SPEED,
        pygame.K_SPACE: BRAKE,
    }

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_p:
                        paused = not paused
                        if paused:
                            await send_command(room, *release_all_command())
                            held.clear()
                            manual_held.clear()
                            logger.info("Paused")
                        else:
                            logger.info("Resumed")
                    elif event.key in MANUAL_KEY_MAP:
                        btn = MANUAL_KEY_MAP[event.key]
                        if btn not in manual_held:
                            manual_held.add(btn)
                            if btn not in held:
                                await send_command(room, *press_command(btn))
                                held.add(btn)
                elif event.type == pygame.KEYUP:
                    if event.key in MANUAL_KEY_MAP:
                        btn = MANUAL_KEY_MAP[event.key]
                        manual_held.discard(btn)

            # Grab latest frame
            with frame_lock:
                frame = latest_frame["frame"]

            # Kick off inference in background thread (non-blocking)
            if frame is not None and inference_future is None:
                inference_future = loop.run_in_executor(
                    _inference_pool, run_inference, frame, policy, norm_stats, prev_action_raw, device
                )

            # Collect result if ready (don't block)
            if inference_future is not None and inference_future.done():
                action_np, inference_ms = inference_future.result()
                inference_future = None
                prev_action_raw = torch.from_numpy(action_np).float()

                # Threshold actions to button presses
                ai_pressed: set[int] = set()
                for i, key in enumerate(ACTION_KEYS):
                    btn = ACTION_TO_BUTTON[key]
                    action_values[btn] = float(action_np[i])
                    if action_np[i] > threshold:
                        ai_pressed.add(btn)

                # Resolve opposing directions: forward wins if within 0.2 of down, otherwise higher conf
                if UP in ai_pressed and DOWN in ai_pressed:
                    if action_values[DOWN] - action_values[UP] > 0.2:
                        ai_pressed.discard(UP)
                    else:
                        ai_pressed.discard(DOWN)
                if LEFT in ai_pressed and RIGHT in ai_pressed:
                    if action_values[LEFT] >= action_values[RIGHT]:
                        ai_pressed.discard(RIGHT)
                    else:
                        ai_pressed.discard(LEFT)

                # Only send commands when not paused
                if not paused:
                    # Merge: AI controls direction, manual overrides speed/brake
                    pressed = set()
                    for btn in ai_pressed | manual_held:
                        if btn in (SPEED, BRAKE):
                            if btn in manual_held:
                                pressed.add(btn)
                        else:
                            pressed.add(btn)

                    # Send delta (with debounce: don't release buttons too quickly)
                    now = time.perf_counter()
                    for btn in pressed:
                        press_time[btn] = now
                    for btn in pressed - held:
                        await send_command(room, *press_command(btn))
                    for btn in held - pressed:
                        if now - press_time.get(btn, 0) >= DEBOUNCE_S:
                            await send_command(room, *release_command(btn))
                        else:
                            pressed.add(btn)

                    held = pressed
                    step_count += 1

            # Render
            if frame is not None:
                surface = pygame.surfarray.make_surface(
                    np.transpose(frame, (1, 0, 2))
                )
                screen.blit(surface, (0, 0))
            else:
                screen.fill((30, 30, 30))
                waiting = font.render("Waiting for video...", True, (150, 150, 150))
                screen.blit(waiting, (WIDTH // 2 - 120, HEIGHT // 2))

            draw_overlay(screen, font, held, paused, step_count, inference_ms, action_values, threshold)
            pygame.display.flip()
            clock.tick(30)

            await asyncio.sleep(0)
    finally:
        await send_command(room, *release_all_command())
        await room.disconnect()
        pygame.quit()
        logger.info("Disconnected. Released all buttons.")
