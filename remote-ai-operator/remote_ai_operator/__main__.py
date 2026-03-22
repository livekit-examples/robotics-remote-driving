"""Entry point for `remote-ai-operator` CLI."""

import argparse
import asyncio

import torch


def cli():
    parser = argparse.ArgumentParser(
        description="AI-driven remote operator: a trained LeRobot policy drives the car over LiveKit"
    )
    parser.add_argument("--checkpoint", required=True, help="Path to trained policy checkpoint")
    parser.add_argument("--device", default=None, help="Device: cuda, mps, cpu (auto-detected)")
    parser.add_argument("--threshold", type=float, default=0.5, help="Action threshold (default: 0.5)")
    parser.add_argument("--room", metavar="NAME", help="Override LIVEKIT_ROOM from env")
    args = parser.parse_args()

    device = args.device
    if device is None:
        if torch.cuda.is_available():
            device = "cuda"
        elif torch.backends.mps.is_available():
            device = "mps"
        else:
            device = "cpu"

    from remote_ai_operator.main import main

    try:
        asyncio.run(main(
            checkpoint_path=args.checkpoint,
            device=device,
            threshold=args.threshold,
            room_override=args.room,
        ))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    cli()
