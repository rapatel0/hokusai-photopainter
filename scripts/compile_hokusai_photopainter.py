#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests
from PIL import Image, ImageOps


ROOT = Path("hokusai_photopainter")
ORIGINALS_DIR = ROOT / "originals"
DISPLAY_DIR = ROOT / "photopainter_800x480_bmp"
PREVIEW_DIR = ROOT / "preview_800x480_jpg"
METADATA_DIR = ROOT / "metadata"

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "hokusai-photopainter-compiler/1.0 "
        "(personal open-access museum image archive)"
    }
)

PRINT_HINTS = (
    "print",
    "woodblock",
    "woodcut",
    "surimono",
    "ukiyo",
    "nishiki",
    "oban",
    "chuban",
    "hashira",
    "engraving",
)

E6_PALETTE = [
    (255, 255, 255),  # white
    (0, 0, 0),  # black
    (0, 255, 0),  # green
    (0, 0, 255),  # blue
    (255, 0, 0),  # red
    (255, 255, 0),  # yellow
]


@dataclass(frozen=True)
class HokusaiImage:
    source: str
    source_id: str
    title: str
    date: str | None
    artist: str | None
    medium: str | None
    classification: str | None
    object_url: str
    download_url: str
    high_res_url: str | None
    license_status: str | None


def get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    for attempt in range(4):
        response = SESSION.get(url, params=params, timeout=45)
        if response.status_code in {429, 500, 502, 503, 504} and attempt < 3:
            time.sleep(2**attempt)
            continue
        response.raise_for_status()
        return response.json()
    raise RuntimeError(f"failed to fetch JSON: {url}")


def try_get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
    try:
        return get_json(url, params)
    except requests.HTTPError as exc:
        print(f"Skipping blocked API record: {url} ({exc})", flush=True)
        return None


def is_hokusai_artist(text: str | None) -> bool:
    if not text:
        return False
    lowered = text.lower()
    return "hokusai" in lowered or "katsushika" in lowered


def looks_like_print(*parts: str | None) -> bool:
    haystack = " ".join(part or "" for part in parts).lower()
    return any(hint in haystack for hint in PRINT_HINTS)


def fetch_cleveland() -> list[HokusaiImage]:
    data = get_json(
        "https://openaccess-api.clevelandart.org/api/artworks/",
        {
            "q": "Hokusai",
            "has_image": 1,
            "cc0": "",
            "limit": 1000,
        },
    )
    rows: list[HokusaiImage] = []
    for item in data.get("data", []):
        creators = item.get("creators") or []
        artist = "; ".join(c.get("description") or c.get("name") or "" for c in creators)
        medium = item.get("technique") or item.get("medium")
        classification = item.get("type") or item.get("classification")
        if not is_hokusai_artist(artist or item.get("tombstone")):
            continue
        if not looks_like_print(medium, classification, item.get("title")):
            continue

        images = item.get("images") or {}
        print_img = images.get("print") or {}
        web_img = images.get("web") or {}
        full_img = images.get("full") or {}
        chosen = print_img or web_img or full_img
        download_url = chosen.get("url")
        if not download_url:
            continue

        rows.append(
            HokusaiImage(
                source="cleveland",
                source_id=item.get("accession_number") or str(item.get("id") or ""),
                title=item.get("title") or "",
                date=item.get("creation_date"),
                artist=artist or None,
                medium=medium,
                classification=classification,
                object_url=item.get("url") or "",
                download_url=download_url,
                high_res_url=full_img.get("url"),
                license_status=item.get("share_license_status"),
            )
        )
    return rows


def fetch_artic() -> list[HokusaiImage]:
    rows: list[HokusaiImage] = []
    page = 1
    while True:
        data = get_json(
            "https://api.artic.edu/api/v1/artworks/search",
            {
                "q": 'artist_title:"Katsushika Hokusai"',
                "fields": (
                    "id,title,image_id,artist_display,is_public_domain,"
                    "classification_titles,medium_display,main_reference_number,date_display"
                ),
                "limit": 100,
                "page": page,
            },
        )
        for item in data.get("data", []):
            if not item.get("is_public_domain") or not item.get("image_id"):
                continue
            artist = item.get("artist_display")
            medium = item.get("medium_display")
            classification = "; ".join(item.get("classification_titles") or [])
            if not is_hokusai_artist(artist):
                continue
            if not looks_like_print(medium, classification, item.get("title")):
                continue

            image_id = item["image_id"]
            object_id = str(item["id"])
            rows.append(
                HokusaiImage(
                    source="artic",
                    source_id=item.get("main_reference_number") or object_id,
                    title=item.get("title") or "",
                    date=item.get("date_display"),
                    artist=artist,
                    medium=medium,
                    classification=classification,
                    object_url=f"https://www.artic.edu/artworks/{object_id}",
                    download_url=f"https://www.artic.edu/iiif/2/{image_id}/full/1686,/0/default.jpg",
                    high_res_url=f"https://www.artic.edu/iiif/2/{image_id}/full/full/0/default.jpg",
                    license_status="public_domain",
                )
            )

        pagination = data.get("pagination") or {}
        if page >= int(pagination.get("total_pages") or page):
            break
        page += 1
        time.sleep(0.2)
    return rows


def fetch_met() -> list[HokusaiImage]:
    rows: list[HokusaiImage] = []
    search_data = get_json(
        "https://collectionapi.metmuseum.org/public/collection/v1/search",
        {
            "artistOrCulture": "true",
            "hasImages": "true",
            "q": "Hokusai",
        },
    )
    object_ids = search_data.get("objectIDs") or []
    for index, object_id in enumerate(object_ids, start=1):
        item = try_get_json(
            f"https://collectionapi.metmuseum.org/public/collection/v1/objects/{object_id}"
        )
        if not item:
            continue
        if not item.get("isPublicDomain") or not item.get("primaryImage"):
            continue
        artist = item.get("artistDisplayName")
        medium = item.get("medium")
        classification = item.get("classification") or item.get("objectName")
        if not is_hokusai_artist(artist):
            continue
        if not looks_like_print(medium, classification, item.get("title")):
            continue

        rows.append(
            HokusaiImage(
                source="met",
                source_id=str(item.get("accessionNumber") or item.get("objectID") or ""),
                title=item.get("title") or "",
                date=item.get("objectDate"),
                artist=artist,
                medium=medium,
                classification=classification,
                object_url=item.get("objectURL") or "",
                download_url=item["primaryImage"],
                high_res_url=item["primaryImage"],
                license_status="public_domain",
            )
        )
        if index % 25 == 0:
            time.sleep(0.2)
    return rows


def unique_rows(rows: Iterable[HokusaiImage]) -> list[HokusaiImage]:
    seen: dict[tuple[str, str], HokusaiImage] = {}
    for row in rows:
        seen[(row.source, row.source_id)] = row
    return sorted(seen.values(), key=lambda row: (row.source, row.title.lower(), row.source_id))


def slugify(value: str, max_len: int = 90) -> str:
    value = re.sub(r"[^\w\s.-]+", "", value, flags=re.ASCII)
    value = re.sub(r"\s+", "-", value.strip().lower())
    value = value.strip(".-_")
    return (value or "untitled")[:max_len].strip(".-_")


def row_stem(row: HokusaiImage, index: int) -> str:
    source_id = slugify(row.source_id, 32)
    title = slugify(row.title, 80)
    return f"{index:04d}_{row.source}_{source_id}_{title}"


def extension_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp"):
        if path.endswith(ext):
            return ".jpg" if ext == ".jpeg" else ext
    return ".jpg"


def download_file(url: str, output_path: Path) -> None:
    if output_path.exists() and output_path.stat().st_size > 0:
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with SESSION.get(url, stream=True, timeout=90) as response:
        response.raise_for_status()
        with tmp_path.open("wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 128):
                if chunk:
                    f.write(chunk)
    tmp_path.replace(output_path)


def build_palette_image() -> Image.Image:
    palette = Image.new("P", (1, 1))
    values: list[int] = []
    for color in E6_PALETTE:
        values.extend(color)
    values.extend([255, 255, 255] * (256 - len(E6_PALETTE)))
    palette.putpalette(values)
    return palette


def prepare_display_image(input_path: Path) -> Image.Image:
    with Image.open(input_path) as img:
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        img.thumbnail((800, 480), Image.Resampling.LANCZOS)
        canvas = Image.new("RGB", (800, 480), (255, 255, 255))
        x = (800 - img.width) // 2
        y = (480 - img.height) // 2
        canvas.paste(img, (x, y))
        return canvas


def convert_for_photopainter(input_path: Path, bmp_path: Path, preview_path: Path) -> None:
    if bmp_path.exists() and preview_path.exists():
        return
    bmp_path.parent.mkdir(parents=True, exist_ok=True)
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    display = prepare_display_image(input_path)
    preview = display.copy()
    palette = build_palette_image()
    dithered = display.quantize(palette=palette, dither=Image.Dither.FLOYDSTEINBERG).convert(
        "RGB"
    )
    dithered.save(bmp_path, format="BMP")
    preview.save(preview_path, format="JPEG", quality=88, optimize=True)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifests(records: list[dict[str, Any]]) -> None:
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = METADATA_DIR / "hokusai_photopainter_manifest.csv"
    jsonl_path = METADATA_DIR / "hokusai_photopainter_manifest.jsonl"
    if not records:
        return
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        writer.writeheader()
        writer.writerows(records)
    with jsonl_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> None:
    ROOT.mkdir(exist_ok=True)
    rows = unique_rows([*fetch_cleveland(), *fetch_artic(), *fetch_met()])
    print(f"Found {len(rows)} official public-domain Hokusai print image records", flush=True)

    records: list[dict[str, Any]] = []
    failures: list[tuple[HokusaiImage, str]] = []
    for index, row in enumerate(rows, start=1):
        stem = row_stem(row, index)
        original_path = ORIGINALS_DIR / row.source / f"{stem}{extension_from_url(row.download_url)}"
        bmp_path = DISPLAY_DIR / f"{stem}.bmp"
        preview_path = PREVIEW_DIR / f"{stem}.jpg"
        try:
            download_file(row.download_url, original_path)
            convert_for_photopainter(original_path, bmp_path, preview_path)
            record = {
                **asdict(row),
                "original_path": str(original_path),
                "photopainter_bmp_path": str(bmp_path),
                "preview_jpg_path": str(preview_path),
                "original_sha256": file_sha256(original_path),
            }
            records.append(record)
        except Exception as exc:
            failures.append((row, repr(exc)))
        if index % 25 == 0 or index == len(rows):
            print(f"Processed {index}/{len(rows)}; failures={len(failures)}", flush=True)

    write_manifests(records)
    if failures:
        failure_path = METADATA_DIR / "failures.jsonl"
        with failure_path.open("w", encoding="utf-8") as f:
            for row, error in failures:
                f.write(json.dumps({"row": asdict(row), "error": error}, ensure_ascii=False) + "\n")
        print(f"Wrote failures to {failure_path}", flush=True)
    print(f"Wrote {len(records)} processed images to {DISPLAY_DIR}", flush=True)


if __name__ == "__main__":
    main()
