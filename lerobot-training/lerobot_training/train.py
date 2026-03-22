"""Train a LeRobot policy on a converted driving dataset.

Usage:
    uv run lerobot-train-policy --dataset ./my_dataset --policy act --output ./outputs
    uv run lerobot-train-policy --dataset ./my_dataset --policy diffusion --steps 50000
"""

import argparse
import subprocess
import sys


def cli():
    parser = argparse.ArgumentParser(
        description="Train a LeRobot policy on a driving dataset"
    )
    parser.add_argument("--dataset", required=True, help="Path to LeRobot dataset directory")
    parser.add_argument(
        "--policy", default="act", choices=["act", "diffusion", "vqbet"],
        help="Policy type (default: act)",
    )
    parser.add_argument("--output", default="./outputs/train", help="Output directory for checkpoints")
    parser.add_argument("--steps", type=int, default=100000, help="Training steps (default: 100000)")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size (default: 8)")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate (default: 1e-4)")
    parser.add_argument("--device", default=None, help="Device: cuda, mps, cpu (auto-detected)")
    parser.add_argument("--wandb", action="store_true", help="Enable Weights & Biases logging")
    parser.add_argument("--resume", metavar="PATH", help="Resume from checkpoint path")
    args = parser.parse_args()

    # Build lerobot train command
    cmd = [
        sys.executable, "-m", "lerobot.scripts.train",
        f"--dataset.repo_id={args.dataset}",
        f"--dataset.local_files_only=true",
        f"--policy.type={args.policy}",
        f"--output_dir={args.output}",
        f"--training.num_train_steps={args.steps}",
        f"--training.batch_size={args.batch_size}",
        f"--optimizer.lr={args.lr}",
    ]

    if args.device:
        cmd.append(f"--policy.device={args.device}")

    if args.wandb:
        cmd.append("--wandb.enable=true")

    if args.resume:
        cmd.append(f"--config_path={args.resume}")
        cmd.append("--resume=true")

    print(f"Running: {' '.join(cmd)}")
    sys.exit(subprocess.call(cmd))


if __name__ == "__main__":
    cli()
