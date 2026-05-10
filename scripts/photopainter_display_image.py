#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from PIL import Image, ImageOps
from waveshare_epd import epd7in3e


def fit_image(path: Path, width: int, height: int, rotate: int = 0) -> Image.Image:
    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((width, height), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (width, height), (255, 255, 255))
        canvas.paste(img, ((width - img.width) // 2, (height - img.height) // 2))
        if rotate:
            canvas = canvas.rotate(rotate, expand=False)
        return canvas


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path, help="Image to render on the PhotoPainter display")
    parser.add_argument("--clear-first", action="store_true")
    parser.add_argument("--rotate", type=int, choices=(0, 90, 180, 270), default=180)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

    epd = epd7in3e.EPD()
    image = fit_image(args.image, epd.width, epd.height, args.rotate)

    logging.info("initializing display")
    epd.init()
    if args.clear_first:
        logging.info("clearing display")
        epd.Clear()

    logging.info("displaying %s", args.image)
    epd.display(epd.getbuffer(image))
    logging.info("sleeping display")
    epd.sleep()


if __name__ == "__main__":
    main()
