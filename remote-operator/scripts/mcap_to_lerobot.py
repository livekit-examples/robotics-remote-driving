#!/usr/bin/env python3
"""Convert MCAP episodes recorded by remote-operator to LeRobot v3.0 dataset format.

Usage:
    python mcap_to_lerobot.py --input episode_*.mcap --output ./my_dataset --fps 10

Requires: pip install mcap Pillow pandas pyarrow
Also requires ffmpeg in PATH for video encoding.
"""

import argparse
import io
import json
import shutil
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from mcap.reader import make_reader
from PIL import Image


ACTION_KEYS = ["w", "a", "s", "d", "speed", "brake"]


def read_mcap_episode(mcap_path: Path) -> tuple[list[Image.Image], list[dict]]:
    """Read an MCAP file and return paired (frames, controls)."""
    frames: list[Image.Image] = []
    controls: list[dict] = []

    with open(mcap_path, "rb") as f:
        reader = make_reader(f)
        for schema, channel, message in reader.iter_messages():
            if channel.topic == "/camera":
                img = Image.open(io.BytesIO(message.data))
                frames.append(img.convert("RGB"))
            elif channel.topic == "/controls":
                ctrl = json.loads(message.data.decode())
                controls.append(ctrl)

    # Pair 1:1 — take the minimum length if somehow mismatched
    n = min(len(frames), len(controls))
    return frames[:n], controls[:n]


def encode_video(frames: list[Image.Image], output_path: Path, fps: int) -> None:
    """Encode frames to MP4 using ffmpeg."""
    if not frames:
        return

    h, w = frames[0].height, frames[0].width
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg", "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{w}x{h}",
        "-pix_fmt", "rgb24",
        "-r", str(fps),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-crf", "23",
        "-preset", "fast",
        str(output_path),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    for frame in frames:
        proc.stdin.write(np.array(frame).tobytes())
    proc.stdin.close()
    proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {proc.stderr.read().decode()}")


def build_dataset(
    mcap_paths: list[Path],
    output_dir: Path,
    fps: int,
    task: str,
) -> None:
    """Build a LeRobot v3.0 dataset from MCAP episodes."""
    output_dir.mkdir(parents=True, exist_ok=True)

    all_rows = []
    episode_lengths = []
    global_index = 0

    for ep_idx, mcap_path in enumerate(sorted(mcap_paths)):
        print(f"Processing episode {ep_idx}: {mcap_path.name}")
        frames, controls = read_mcap_episode(mcap_path)

        if not frames:
            print(f"  Skipping (empty)")
            continue

        # Encode video
        video_path = output_dir / "videos" / "observation.images.camera" / f"chunk-000/episode_{ep_idx:06d}.mp4"
        encode_video(frames, video_path, fps)

        # Build rows
        for frame_idx, ctrl in enumerate(controls):
            action = [float(ctrl.get(k, False)) for k in ACTION_KEYS]
            all_rows.append({
                "index": global_index,
                "episode_index": ep_idx,
                "frame_index": frame_idx,
                "timestamp": frame_idx / fps,
                "action": action,
                "task_index": 0,
            })
            global_index += 1

        episode_lengths.append(len(controls))
        print(f"  {len(frames)} frames")

    if not all_rows:
        print("No data to write.")
        return

    # Write data parquet
    data_dir = output_dir / "data" / "chunk-000"
    data_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(all_rows)
    table = pa.table({
        "index": pa.array(df["index"].tolist(), type=pa.int64()),
        "episode_index": pa.array(df["episode_index"].tolist(), type=pa.int64()),
        "frame_index": pa.array(df["frame_index"].tolist(), type=pa.int64()),
        "timestamp": pa.array(df["timestamp"].tolist(), type=pa.float32()),
        "action": pa.array(df["action"].tolist(), type=pa.list_(pa.float32())),
        "task_index": pa.array(df["task_index"].tolist(), type=pa.int64()),
    })
    pq.write_table(table, data_dir / "file-000.parquet")

    # Write episode parquets
    ep_meta_dir = output_dir / "meta" / "episodes" / "chunk-000"
    ep_meta_dir.mkdir(parents=True, exist_ok=True)

    ep_rows = []
    for ep_idx, length in enumerate(episode_lengths):
        ep_rows.append({"episode_index": ep_idx, "length": length, "task_index": 0})
    ep_table = pa.table({
        "episode_index": pa.array([r["episode_index"] for r in ep_rows], type=pa.int64()),
        "length": pa.array([r["length"] for r in ep_rows], type=pa.int64()),
        "task_index": pa.array([r["task_index"] for r in ep_rows], type=pa.int64()),
    })
    pq.write_table(ep_table, ep_meta_dir / "file-000.parquet")

    # Write tasks parquet
    meta_dir = output_dir / "meta"
    tasks_table = pa.table({
        "task_index": pa.array([0], type=pa.int64()),
        "task": pa.array([task], type=pa.string()),
    })
    pq.write_table(tasks_table, meta_dir / "tasks.parquet")

    # Compute stats
    actions = np.array([r["action"] for r in all_rows], dtype=np.float32)
    stats = {
        "action": {
            "mean": actions.mean(axis=0).tolist(),
            "std": actions.std(axis=0).tolist(),
            "min": actions.min(axis=0).tolist(),
            "max": actions.max(axis=0).tolist(),
        }
    }

    # Get frame size from first episode
    h, w = 480, 640
    if episode_lengths:
        first_frames, _ = read_mcap_episode(sorted(mcap_paths)[0])
        if first_frames:
            h, w = first_frames[0].height, first_frames[0].width

    # Write info.json
    info = {
        "codebase_version": "v3.0",
        "robot_type": "rc_car",
        "fps": fps,
        "total_episodes": len(episode_lengths),
        "total_frames": global_index,
        "features": {
            "observation.images.camera": {
                "dtype": "video",
                "shape": [h, w, 3],
                "names": ["height", "width", "channels"],
                "info": {
                    "codec": "libx264",
                    "pix_fmt": "yuv420p",
                    "is_depth_map": False,
                },
            },
            "action": {
                "dtype": "float32",
                "shape": [6],
                "names": ["forward", "backward", "left", "right", "speed", "brake"],
            },
            "timestamp": {"dtype": "float32", "shape": [1]},
            "frame_index": {"dtype": "int64", "shape": [1]},
            "episode_index": {"dtype": "int64", "shape": [1]},
            "index": {"dtype": "int64", "shape": [1]},
            "task_index": {"dtype": "int64", "shape": [1]},
        },
    }

    with open(meta_dir / "info.json", "w") as f:
        json.dump(info, f, indent=2)

    with open(meta_dir / "stats.json", "w") as f:
        json.dump(stats, f, indent=2)

    print(f"\nDataset written to {output_dir}")
    print(f"  Episodes: {len(episode_lengths)}")
    print(f"  Total frames: {global_index}")


def main():
    parser = argparse.ArgumentParser(description="Convert MCAP episodes to LeRobot dataset")
    parser.add_argument("--input", nargs="+", required=True, help="MCAP file(s)")
    parser.add_argument("--output", required=True, help="Output dataset directory")
    parser.add_argument("--fps", type=int, default=10, help="Recording FPS (default: 10)")
    parser.add_argument("--task", default="drive", help="Task description (default: 'drive')")
    args = parser.parse_args()

    mcap_paths = [Path(p) for p in args.input]
    for p in mcap_paths:
        if not p.exists():
            raise FileNotFoundError(f"MCAP file not found: {p}")

    build_dataset(mcap_paths, Path(args.output), args.fps, args.task)


if __name__ == "__main__":
    main()
