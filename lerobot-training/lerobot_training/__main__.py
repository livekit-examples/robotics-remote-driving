"""Entry point for `python -m lerobot_training`."""

import argparse
import sys


def cli():
    parser = argparse.ArgumentParser(
        description="LeRobot training pipeline for RC car driving",
        usage="%(prog)s <command> [options]",
    )
    parser.add_argument(
        "command",
        choices=["convert", "train", "infer"],
        help="convert: MCAP → LeRobot dataset, train: train a policy, infer: run policy over LiveKit",
    )
    args, remaining = parser.parse_known_args()

    # Re-inject remaining args so subcommand parsers see them
    sys.argv = [f"lerobot-{args.command}"] + remaining

    if args.command == "convert":
        from lerobot_training.convert import cli as convert_cli
        convert_cli()
    elif args.command == "train":
        from lerobot_training.train import cli as train_cli
        train_cli()
    elif args.command == "infer":
        from lerobot_training.infer import cli as infer_cli
        infer_cli()


if __name__ == "__main__":
    cli()
