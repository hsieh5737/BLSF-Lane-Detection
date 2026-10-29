"""Dataset adapters. Each item: key, image path, group (calibration group), GT lanes.

GT lanes are lists of (x, y) image-pixel points. Only adapters listed here are
supported; the protocol fixes which lists are evaluated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Item:
    key: str            # dataset-relative path, unique
    image: Path
    group: str          # selects the homography (e.g. CULane driver folder)
    lanes: list = field(default_factory=list)


def read_culane_lines(path: Path):
    lanes = []
    if not path.exists():
        raise FileNotFoundError(f"missing CULane annotation {path}")
    for line in path.read_text().split("\n"):
        vals = line.split()
        if not vals:
            continue
        nums = [float(v) for v in vals]
        if len(nums) % 2:
            raise ValueError(f"odd coordinate count in {path}")
        pts = [(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)]
        pts = [p for p in pts if p[0] >= 0 and p[1] >= 0]
        if len(pts) >= 2:
            lanes.append(pts)
    return lanes


def culane_items(root: Path, list_file: Path, exclude=()):
    """Items of a CULane list (e.g. list/test_split/test8_night.txt)."""
    root = Path(root)
    excl = {e.strip().lstrip("/") for e in exclude}
    items = []
    for raw in Path(list_file).read_text().split("\n"):
        rel = raw.strip().split()[0] if raw.strip() else ""
        if not rel:
            continue
        rel = rel.lstrip("/")
        if rel in excl:
            continue
        img = root / rel
        ann = img.with_suffix(".lines.txt")
        items.append(Item(key=rel, image=img, group=rel.split("/")[0],
                          lanes=read_culane_lines(ann)))
    keys = [i.key for i in items]
    if len(set(keys)) != len(keys):
        raise ValueError(f"duplicate entries in {list_file}")
    return items


ADAPTERS = {"culane": culane_items}
