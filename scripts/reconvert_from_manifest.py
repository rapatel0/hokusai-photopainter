#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import compile_hokusai_photopainter as compiler


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "metadata" / "hokusai_photopainter_manifest.jsonl"


def repo_path(value: str) -> Path:
    path = Path(value)
    if path.parts and path.parts[0] == ROOT.name:
        path = Path(*path.parts[1:])
    return ROOT / path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild display BMPs from existing originals and manifest."
    )
    parser.add_argument(
        "--conversion",
        choices=("waveshare", "waveshare-crop", "adaptive", "plain"),
        default="waveshare",
    )
    parser.add_argument("--force", action="store_true", default=True)
    parser.add_argument("--no-force", dest="force", action="store_false")
    parser.add_argument(
        "--no-paper-cleanup",
        dest="paper_cleanup",
        action="store_false",
        default=True,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not MANIFEST.exists():
        raise SystemExit(f"Missing manifest: {MANIFEST}")

    rows = [
        json.loads(line)
        for line in MANIFEST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    failures = 0
    for index, record in enumerate(rows, start=1):
        original_path = repo_path(record["original_path"])
        bmp_path = repo_path(record["photopainter_bmp_path"])
        preview_path = repo_path(record["preview_jpg_path"])
        if not original_path.exists():
            print(f"missing original: {original_path}", file=sys.stderr)
            failures += 1
            continue

        compiler.convert_for_photopainter(
            original_path,
            bmp_path,
            preview_path,
            force=args.force,
            prequantize=False,
            paper_cleanup=args.paper_cleanup,
            conversion=args.conversion,
        )
        if index % 50 == 0 or index == len(rows):
            print(f"reconverted {index}/{len(rows)}", flush=True)

    if failures:
        raise SystemExit(f"Failed to reconvert {failures} images")


if __name__ == "__main__":
    main()
