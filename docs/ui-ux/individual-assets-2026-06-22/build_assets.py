#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import math
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

OUT_DIR = Path(__file__).resolve().parent
REPO = OUT_DIR.parents[2]
UI_UX = REPO / "docs" / "ui-ux"
ASSET_DIR = OUT_DIR / "assets"
MANIFEST = OUT_DIR / "manifest.tsv"
ALIASES = OUT_DIR / "aliases.tsv"

EXPECTED_MOCKUPS = 41
EXPECTED_REFERENCES = 45
EXPECTED_ALIASES = 10

SCALE = 0.30
MAX_FILTER_SIZE = 7
PADDING = 12
MIN_WIDTH = 80
MIN_HEIGHT = 60
MIN_AREA = 30000


@dataclass(frozen=True)
class Source:
    group: str
    index: str
    path: Path
    sha256: str


def rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def natural_key(path: Path) -> tuple[object, ...]:
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", path.name))


def iter_pixels(img: Image.Image):
    if hasattr(img, "get_flattened_data"):
        return img.get_flattened_data()
    return img.getdata()


def discover_sources() -> tuple[list[Source], dict[str, list[Path]]]:
    mockups = sorted((UI_UX / "mockups").glob("mockup_*.png"), key=natural_key)
    references = sorted(
        (UI_UX / "reference-set-2026-06-18" / "images").glob("ui-ux-reference-*.png"),
        key=natural_key,
    )
    branding_aliases = sorted((REPO / "frontend" / "branding").glob("naruon-ux-mockup-*.png"), key=natural_key)

    if len(mockups) != EXPECTED_MOCKUPS:
        raise SystemExit(f"expected {EXPECTED_MOCKUPS} mockups, found {len(mockups)}")
    if len(references) != EXPECTED_REFERENCES:
        raise SystemExit(f"expected {EXPECTED_REFERENCES} reference images, found {len(references)}")
    if len(branding_aliases) != EXPECTED_ALIASES:
        raise SystemExit(f"expected {EXPECTED_ALIASES} branding aliases, found {len(branding_aliases)}")

    sources: list[Source] = []
    seen: dict[str, Source] = {}
    aliases: dict[str, list[Path]] = {}
    for group, paths in (("mockups", mockups), ("reference-set-2026-06-18", references)):
        for path in paths:
            digest = sha256(path)
            index = re.search(r"(\d+)", path.stem)
            source = Source(group=group, index=index.group(1) if index else path.stem, path=path, sha256=digest)
            if digest in seen:
                aliases.setdefault(digest, []).append(path)
                continue
            seen[digest] = source
            sources.append(source)

    for path in branding_aliases:
        digest = sha256(path)
        if digest not in seen:
            raise SystemExit(f"branding alias has no canonical source: {rel(path)}")
        aliases.setdefault(digest, []).append(path)

    validate_reference_sources()
    return sources, aliases


def validate_reference_sources() -> None:
    sources_tsv = UI_UX / "reference-set-2026-06-18" / "sources.tsv"
    rows = list(csv.reader(sources_tsv.open(newline=""), delimiter="\t"))
    if len(rows) != EXPECTED_REFERENCES:
        raise SystemExit(f"sources.tsv row count mismatch: {len(rows)}")
    for index, digest, source_path in rows:
        path = REPO / source_path
        if sha256(path) != digest:
            raise SystemExit(f"sources.tsv SHA mismatch: {source_path}")
        if index != re.search(r"(\d+)", path.stem).group(1):
            raise SystemExit(f"sources.tsv index mismatch: {source_path}")


def foreground_mask(img: Image.Image) -> Image.Image:
    mask = []
    for r, g, b, a in iter_pixels(img):
        dist = max(255 - r, 255 - g, 255 - b)
        sat = max(r, g, b) - min(r, g, b)
        mask.append(255 if a > 0 and (dist > 24 or (dist > 12 and sat > 12)) else 0)
    out = Image.new("L", img.size)
    out.putdata(mask)
    return out.filter(ImageFilter.MaxFilter(MAX_FILTER_SIZE))


def components(mask: bytes, width: int, height: int) -> list[tuple[int, int, int, int]]:
    data = bytearray(mask)
    boxes: list[tuple[int, int, int, int]] = []
    for start, value in enumerate(data):
        if not value:
            continue
        stack = [start]
        data[start] = 0
        min_x = max_x = start % width
        min_y = max_y = start // width
        for current in stack:
            x = current % width
            y = current // width
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if nx < 0 or nx >= width or ny < 0 or ny >= height:
                    continue
                ni = ny * width + nx
                if not data[ni]:
                    continue
                data[ni] = 0
                stack.append(ni)
                min_x = min(min_x, nx)
                max_x = max(max_x, nx)
                min_y = min(min_y, ny)
                max_y = max(max_y, ny)
        boxes.append((min_x, min_y, max_x + 1, max_y + 1))
    return boxes


def split_boxes(img: Image.Image) -> list[tuple[int, int, int, int]]:
    small = img.resize((max(1, round(img.width * SCALE)), max(1, round(img.height * SCALE))), Image.Resampling.BILINEAR)
    mask = foreground_mask(small)
    boxes: list[tuple[int, int, int, int]] = []
    for x0, y0, x1, y1 in components(mask.tobytes(), small.width, small.height):
        fx0 = max(0, math.floor(x0 / SCALE) - PADDING)
        fy0 = max(0, math.floor(y0 / SCALE) - PADDING)
        fx1 = min(img.width, math.ceil(x1 / SCALE) + PADDING)
        fy1 = min(img.height, math.ceil(y1 / SCALE) + PADDING)
        width = fx1 - fx0
        height = fy1 - fy0
        if width >= MIN_WIDTH and height >= MIN_HEIGHT and width * height >= MIN_AREA:
            boxes.append((fx0, fy0, width, height))
    # ponytail: faint future art still gets one reviewable asset instead of silently vanishing.
    return sorted(boxes or [(0, 0, img.width, img.height)], key=lambda box: (box[1], box[0]))


def asset_kind(crop_area: int, source_area: int) -> str:
    ratio = crop_area / source_area
    if ratio >= 0.18:
        return "screen-panel"
    if ratio >= 0.08:
        return "panel"
    if ratio >= 0.035:
        return "component"
    return "control-annotation"


def generate() -> None:
    sources, aliases = discover_sources()
    if ASSET_DIR.exists():
        shutil.rmtree(ASSET_DIR)
    ASSET_DIR.mkdir(parents=True)

    manifest_rows: list[dict[str, str]] = []
    for source in sources:
        img = Image.open(source.path).convert("RGBA")
        source_area = img.width * img.height
        source_alias_paths = ";".join(rel(path) for path in sorted(aliases.get(source.sha256, []), key=natural_key))
        for part, (x, y, width, height) in enumerate(split_boxes(img), start=1):
            kind = asset_kind(width * height, source_area)
            source_slug = source.path.stem
            asset_id = f"{source.group}-{source.index}-asset-{part:03d}"
            asset_path = ASSET_DIR / source.group / source_slug / f"{source_slug}_asset_{part:03d}_{kind}.png"
            asset_path.parent.mkdir(parents=True, exist_ok=True)
            img.crop((x, y, x + width, y + height)).save(asset_path, optimize=True, compress_level=9)
            manifest_rows.append(
                {
                    "asset_id": asset_id,
                    "asset_kind": kind,
                    "asset_label": f"{source_slug} {kind.replace('-', ' ')} {part:03d}",
                    "source_group": source.group,
                    "source_index": source.index,
                    "source_path": rel(source.path),
                    "source_sha256": source.sha256,
                    "source_width": str(img.width),
                    "source_height": str(img.height),
                    "crop_x": str(x),
                    "crop_y": str(y),
                    "crop_width": str(width),
                    "crop_height": str(height),
                    "asset_path": rel(asset_path),
                    "asset_sha256": sha256(asset_path),
                    "source_alias_paths": source_alias_paths,
                    "notes": "foreground-component-heuristic",
                }
            )

    write_tsv(MANIFEST, manifest_rows)
    write_aliases(sources, aliases, manifest_rows)
    verify()


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_aliases(sources: list[Source], aliases: dict[str, list[Path]], manifest_rows: list[dict[str, str]]) -> None:
    by_sha = {source.sha256: source for source in sources}
    count_by_sha: dict[str, int] = {}
    for row in manifest_rows:
        count_by_sha[row["source_sha256"]] = count_by_sha.get(row["source_sha256"], 0) + 1
    rows = []
    for digest, paths in aliases.items():
        source = by_sha[digest]
        for path in sorted(paths, key=natural_key):
            rows.append(
                {
                    "alias_path": rel(path),
                    "alias_sha256": digest,
                    "canonical_source_path": rel(source.path),
                    "canonical_source_sha256": source.sha256,
                    "canonical_asset_count": str(count_by_sha[source.sha256]),
                    "canonical_manifest_selector": f"source_sha256={source.sha256}",
                }
            )
    write_tsv(ALIASES, rows)


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def verify() -> None:
    sources, aliases = discover_sources()
    manifest_rows = read_tsv(MANIFEST)
    alias_rows = read_tsv(ALIASES)
    if len(alias_rows) != EXPECTED_ALIASES:
        raise SystemExit(f"alias row count mismatch: {len(alias_rows)}")

    source_by_path = {rel(source.path): source for source in sources}
    rows_by_source: dict[str, list[dict[str, str]]] = {}
    asset_paths: set[str] = set()
    for row in manifest_rows:
        source = source_by_path.get(row["source_path"])
        if source is None:
            raise SystemExit(f"unexpected source path in manifest: {row['source_path']}")
        if row["source_sha256"] != source.sha256 or sha256(REPO / row["source_path"]) != source.sha256:
            raise SystemExit(f"source SHA mismatch: {row['source_path']}")
        asset_path = REPO / row["asset_path"]
        if row["asset_path"] in asset_paths:
            raise SystemExit(f"duplicate asset path: {row['asset_path']}")
        asset_paths.add(row["asset_path"])
        if not asset_path.exists() or sha256(asset_path) != row["asset_sha256"]:
            raise SystemExit(f"asset SHA mismatch: {row['asset_path']}")

        img = Image.open(REPO / row["source_path"]).convert("RGBA")
        asset = Image.open(asset_path).convert("RGBA")
        x = int(row["crop_x"])
        y = int(row["crop_y"])
        width = int(row["crop_width"])
        height = int(row["crop_height"])
        if x < 0 or y < 0 or width <= 0 or height <= 0 or x + width > img.width or y + height > img.height:
            raise SystemExit(f"crop out of bounds: {row['asset_id']}")
        if asset.size != (width, height):
            raise SystemExit(f"asset size mismatch: {row['asset_id']}")
        if ImageChops.difference(asset, img.crop((x, y, x + width, y + height))).getbbox() is not None:
            raise SystemExit(f"asset pixels do not match source crop: {row['asset_id']}")
        rows_by_source.setdefault(row["source_path"], []).append(row)

    missing = sorted(set(source_by_path) - set(rows_by_source))
    if missing:
        raise SystemExit(f"missing sources in manifest: {', '.join(missing)}")

    alias_by_path = {row["alias_path"]: row for row in alias_rows}
    expected_alias_paths = {rel(path) for paths in aliases.values() for path in paths}
    if set(alias_by_path) != expected_alias_paths:
        raise SystemExit("alias path set mismatch")
    for row in alias_rows:
        if row["canonical_source_path"] not in rows_by_source:
            raise SystemExit(f"alias canonical source missing: {row['alias_path']}")
        if row["alias_sha256"] != sha256(REPO / row["alias_path"]):
            raise SystemExit(f"alias SHA mismatch: {row['alias_path']}")
        if row["alias_sha256"] != row["canonical_source_sha256"]:
            raise SystemExit(f"alias canonical SHA mismatch: {row['alias_path']}")

    expected_boxes = {
        rel(source.path): split_boxes(Image.open(source.path).convert("RGBA"))
        for source in sources
    }
    for source_path, rows in rows_by_source.items():
        observed = [
            (int(row["crop_x"]), int(row["crop_y"]), int(row["crop_width"]), int(row["crop_height"]))
            for row in rows
        ]
        if observed != expected_boxes[source_path]:
            raise SystemExit(f"split rule drifted: {source_path}")

    print(
        f"verified {len(manifest_rows)} assets from {len(sources)} canonical sources "
        f"with {len(alias_rows)} exact aliases"
    )


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "verify"
    if command == "generate":
        generate()
    elif command == "verify":
        verify()
    else:
        raise SystemExit("usage: build_assets.py [generate|verify]")


if __name__ == "__main__":
    main()
