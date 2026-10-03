"""
Download YuNet face detection and SFace face recognition ONNX models.
"""
import os
import sys
import urllib.request
from pathlib import Path

from config import (
    MODELS_DIR,
    YUNET_MODEL_PATH,
    SFACE_MODEL_PATH,
    YUNET_DOWNLOAD_URL,
    SFACE_DOWNLOAD_URL,
)


def download_file(url: str, dest_path: Path) -> None:
    """Download a file with download progress logging."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(".tmp")
    print(f"Downloading {dest_path.name} from {url}...")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )

    with urllib.request.urlopen(req) as response:
        total_size = response.length or 0
        block_size = 64 * 1024  # 64 KB
        downloaded = 0

        with open(temp_path, "wb") as f:
            while True:
                chunk = response.read(block_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if total_size > 0:
                    pct = (downloaded / total_size) * 100
                    mb_down = downloaded / (1024 * 1024)
                    mb_total = total_size / (1024 * 1024)
                    sys.stdout.write(f"\r  [{dest_path.name}] {mb_down:.1f}/{mb_total:.1f} MB ({pct:.1f}%)")
                    sys.stdout.flush()

    if temp_path.exists():
        if dest_path.exists():
            dest_path.unlink()
        temp_path.rename(dest_path)
    print(f"\nSuccessfully downloaded: {dest_path.name} ({dest_path.stat().st_size:,} bytes)")


def ensure_models() -> None:
    """Ensure both YuNet and SFace models are downloaded."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # Check YuNet (should be ~232 KB)
    if not YUNET_MODEL_PATH.exists() or YUNET_MODEL_PATH.stat().st_size < 100000:
        download_file(YUNET_DOWNLOAD_URL, YUNET_MODEL_PATH)
    else:
        print(f"Model already present: {YUNET_MODEL_PATH.name}")

    # Check SFace (should be ~38 MB)
    if not SFACE_MODEL_PATH.exists() or SFACE_MODEL_PATH.stat().st_size < 10000000:
        download_file(SFACE_DOWNLOAD_URL, SFACE_MODEL_PATH)
    else:
        print(f"Model already present: {SFACE_MODEL_PATH.name}")


if __name__ == "__main__":
    ensure_models()
