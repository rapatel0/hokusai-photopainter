#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageOps
from waveshare_epd import epd7in3e


DEFAULT_DIR = Path.home() / "Pictures" / "hokusai-photopainter"
DEFAULT_STATE_FILE = DEFAULT_DIR / ".photopainter-state.json"


def fit_image(path: Path, width: int, height: int, rotate: int = 0) -> Image.Image:
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        canvas.paste(img, ((width - img.width) // 2, (height - img.height) // 2))
        if rotate:
            canvas = canvas.rotate(rotate, expand=False)
        return canvas


def load_next_index(state_file: Path, total: int, reset: bool) -> int:
    if reset or not state_file.exists():
        return 0
    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
        return int(state.get("next_index", 0)) % total
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        return 0


def save_next_index(state_file: Path, next_index: int, image_path: Path, total: int) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps(
            {
                "next_index": next_index % total,
                "last_image": image_path.name,
                "total_images": total,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def choose_image(
    image_dir: Path, query: str | None, state_file: Path, reset_state: bool
) -> tuple[Path, int, int]:
    images = sorted(image_dir.glob("*.bmp"))
    if query:
        query_lower = query.lower()
        images = [path for path in images if query_lower in path.name.lower()]
    if not images:
        raise SystemExit(f"No matching BMP images found in {image_dir}")
    index = load_next_index(state_file, len(images), reset_state)
    return images[index], index, len(images)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("query", nargs="?", help="Optional filename search, e.g. wave or fuji")
    parser.add_argument("--dir", type=Path, default=DEFAULT_DIR)
    parser.add_argument("--state-file", type=Path, default=DEFAULT_STATE_FILE)
    parser.add_argument("--reset-state", action="store_true")
    parser.add_argument("--rotate", type=int, choices=(0, 90, 180, 270), default=180)
    parser.add_argument(
        "--clear-first",
        dest="clear_first",
        action="store_true",
        default=False,
        help="Clear the panel before drawing the next image.",
    )
    parser.add_argument(
        "--no-clear-first",
        dest="clear_first",
        action="store_false",
        help="Skip the pre-display clear refresh.",
    )
    args = parser.parse_args()

    image_path, index, total = choose_image(
        args.dir, args.query, args.state_file, args.reset_state
    )
    print(f"{index + 1}/{total}: {image_path}")

    epd = epd7in3e.EPD()
    image = fit_image(image_path, epd.width, epd.height, args.rotate)
    epd.init()
    if args.clear_first:
        epd.Clear()
    epd.display(epd.getbuffer(image))
    epd.sleep()
    save_next_index(args.state_file, index + 1, image_path, total)


if __name__ == "__main__":
    main()
