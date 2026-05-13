#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path
from urllib.request import urlopen


CONVERTER_URL = "https://files.waveshare.com/wiki/common/ConverTo6c_bmp-7.3.zip"
CONVERTER_SHA256 = "82b34215d6d5c9759b82dedc329b78d7e79d73fee1d177bb3287674ce98613d7"
VENDOR_DIR = Path("vendor") / "waveshare-photopainter"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    zip_path = VENDOR_DIR / "ConverTo6c_bmp-7.3.zip"
    if not zip_path.exists():
        with urlopen(CONVERTER_URL, timeout=60) as response:
            with zip_path.open("wb") as f:
                shutil.copyfileobj(response, f)

    actual = sha256(zip_path)
    if actual != CONVERTER_SHA256:
        raise SystemExit(
            f"Unexpected converter checksum for {zip_path}: {actual}"
        )

    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(VENDOR_DIR)

    print(f"Downloaded Waveshare converter to {VENDOR_DIR}")


if __name__ == "__main__":
    main()
