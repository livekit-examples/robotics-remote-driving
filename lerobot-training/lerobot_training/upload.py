"""Upload a local LeRobot dataset to HuggingFace Hub.

Usage:
    python -m lerobot_training upload --dataset ./my_dataset --repo-id username/my-driving-data
    python -m lerobot_training upload --dataset ./my_dataset --repo-id username/my-driving-data --private
"""

import argparse
from pathlib import Path

from huggingface_hub import HfApi, login


def upload_dataset(dataset_dir: Path, repo_id: str, private: bool = False) -> None:
    """Upload a local LeRobot dataset directory to HuggingFace Hub."""
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_dir}")

    info_path = dataset_dir / "meta" / "info.json"
    if not info_path.exists():
        raise FileNotFoundError(f"Not a valid LeRobot dataset (missing meta/info.json): {dataset_dir}")

    api = HfApi()

    # Ensure logged in
    try:
        api.whoami()
    except Exception:
        print("Not logged in to HuggingFace. Running `huggingface-cli login`...")
        login()

    print(f"Creating dataset repo: {repo_id}")
    api.create_repo(repo_id=repo_id, repo_type="dataset", private=private, exist_ok=True)

    print(f"Uploading {dataset_dir} → https://huggingface.co/datasets/{repo_id}")
    api.upload_folder(
        folder_path=str(dataset_dir),
        repo_id=repo_id,
        repo_type="dataset",
    )

    print(f"\nDone! Dataset available at: https://huggingface.co/datasets/{repo_id}")


def cli():
    parser = argparse.ArgumentParser(
        description="Upload a local LeRobot dataset to HuggingFace Hub"
    )
    parser.add_argument("--dataset", required=True, help="Path to local LeRobot dataset directory")
    parser.add_argument("--repo-id", required=True, help="HuggingFace repo ID (e.g. username/dataset-name)")
    parser.add_argument("--private", action="store_true", help="Make the dataset private")
    args = parser.parse_args()

    upload_dataset(Path(args.dataset), args.repo_id, args.private)


if __name__ == "__main__":
    cli()
