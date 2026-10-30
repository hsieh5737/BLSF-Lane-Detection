"""Secondary metric: CULane-style ego-lane IoU in image space.

Follows the official CULane rule (lanes drawn 30 px wide on the 1640x590
image, true positive at IoU >= 0.5) for the two ego boundaries only, inside the
image region covered by the BEV ROI (the method's operating range). Ego GT
lanes are the same lanes selected by the BEV metric (evaluate.gt_ego_lanes).
The prediction x = a y^2 + b y + c is mapped back from the BEV with H^-1.
"""
from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from . import evaluate as ev
from . import geometry as geo


@dataclass
class ImageEvalParams:
    img_w: int = 1640
    img_h: int = 590
    line_width_px: int = 30
    iou_threshold: float = 0.5


def bev_to_image(H, bev_w, bev_h):
    Hinv = np.linalg.inv(H)
    if (Hinv @ np.array([bev_w / 2.0, bev_h / 2.0, 1.0]))[2] < 0:
        Hinv = -Hinv
    return Hinv


def roi_mask(Hinv, bev_w, bev_h, p: ImageEvalParams):
    corners = np.array([[0, 0], [bev_w - 1, 0], [bev_w - 1, bev_h - 1], [0, bev_h - 1]], float)
    poly = geo.warp_points(Hinv, corners)
    m = np.zeros((p.img_h, p.img_w), np.uint8)
    cv2.fillPoly(m, [np.round(poly).astype(np.int32).reshape(-1, 1, 2)], 255)
    return m


def _draw(pts, p: ImageEvalParams):
    m = np.zeros((p.img_h, p.img_w), np.uint8)
    pts = np.asarray(pts, float).reshape(-1, 2)
    pts = pts[np.all(np.isfinite(pts), axis=1)]
    if len(pts) >= 2:
        pts = np.clip(pts, -1e5, 1e5)
        cv2.polylines(m, [np.round(pts).astype(np.int32).reshape(-1, 1, 2)], False, 255,
                      p.line_width_px, cv2.LINE_8)
    return m


def gt_ego_indices(lanes_img, H, bev_w, bev_h, p: ev.EvalParams):
    """Indices of the lanes that the BEV metric selects as ego left / right."""
    cands = []
    for i, lane in enumerate(lanes_img):
        mask = geo.render_polyline(geo.warp_points(H, lane), bev_w, bev_h, p.line_width_px)
        rows = geo.covered_rows(mask)
        if len(rows) < p.min_gt_rows:
            continue
        cands.append((float(np.flatnonzero(mask[rows.max()]).mean()), i))
    mid = bev_w / 2.0
    L = [c for c in cands if c[0] < mid]
    R = [c for c in cands if c[0] >= mid]
    return {"left": max(L)[1] if L else None, "right": min(R)[1] if R else None}


def score_frame_image(pred_row, lanes_img, H, bev_w, bev_h, p_bev: ev.EvalParams, p: ImageEvalParams,
                      roi=None):
    Hinv = bev_to_image(H, bev_w, bev_h)
    if roi is None:
        roi = roi_mask(Hinv, bev_w, bev_h, p)
    idx = gt_ego_indices(lanes_img, H, bev_w, bev_h, p_bev)
    out = {"tp": 0, "fp": 0, "fn": 0}
    for side in ("left", "right"):
        valid = pred_row is not None and pred_row.get(f"{side}_valid") == "1"
        pm = None
        if valid:
            a, b, c = (ev._f(pred_row, f"{side}_{k}") for k in "abc")
            if None in (a, b, c):
                valid = False
            else:
                y = np.arange(bev_h, dtype=float)
                x = a * y * y + b * y + c
                keep = (x >= 0) & (x <= bev_w - 1)
                pts = np.stack([x, y], 1)
                pts[~keep] = np.nan
                pm = _draw(geo.warp_points(Hinv, pts), p) & roi
        g = None if idx[side] is None else (_draw(lanes_img[idx[side]], p) & roi)
        iou = None
        if valid and g is not None:
            inter = np.count_nonzero((pm > 0) & (g > 0))
            union = np.count_nonzero((pm > 0) | (g > 0))
            iou = inter / union if union else 0.0
        hit = iou is not None and iou >= p.iou_threshold
        out[f"img_iou_{side}"] = "" if iou is None else round(iou, 6)
        out["tp"] += int(hit)
        out["fp"] += int(valid and not hit)
        out["fn"] += int(g is not None and not hit)
    out["frame_ok"] = int(out["fp"] == 0 and out["fn"] == 0)
    return out
