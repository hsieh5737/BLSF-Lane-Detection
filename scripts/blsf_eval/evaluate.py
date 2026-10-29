"""Per-frame ego-lane evaluation in the BEV ROI (see docs/EVAL_PROTOCOL.md).

For every frame the annotated lanes are warped into the BEV with the group's
homography. A lane counts as ground truth only if it covers at least
min_gt_rows BEV rows. The ego boundaries are the covered lanes nearest the
BEV centre on each side, measured at each lane's lowest covered row. Each side
is scored independently: the prediction for that side (tracker output
x = a y^2 + b y + c) and the GT lane are rendered with the same width, the
prediction is restricted to the GT lane's rows, and the side is a true positive
when IoU >= iou_threshold. A prediction without GT, or below threshold, is a
false positive; a GT lane without a matching prediction is a false negative.
Frames rejected as low-confidence or failing later stages stay in the
denominator with no prediction.
"""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict

import numpy as np

from . import geometry as geo
from . import stats


@dataclass
class EvalParams:
    line_width_px: int = 10        # 0.5 m at 20 px/m
    iou_threshold: float = 0.5
    min_gt_rows: int = 100
    bootstrap: int = 2000
    seed: int = 20261029


def gt_ego_lanes(lanes_img, H, bev_w, bev_h, p: EvalParams):
    """Return {'left': mask or None, 'right': mask or None}."""
    cands = []
    for lane in lanes_img:
        pts = geo.warp_points(H, lane)
        mask = geo.render_polyline(pts, bev_w, bev_h, p.line_width_px)
        rows = geo.covered_rows(mask)
        if len(rows) < p.min_gt_rows:
            continue
        low = rows.max()
        x_low = float(np.flatnonzero(mask[low]).mean())
        cands.append((x_low, mask))
    mid = bev_w / 2.0
    left = [c for c in cands if c[0] < mid]
    right = [c for c in cands if c[0] >= mid]
    return {"left": max(left, key=lambda c: c[0])[1] if left else None,
            "right": min(right, key=lambda c: c[0])[1] if right else None}


def side_iou(pred_mask, gt_mask):
    rows = geo.covered_rows(gt_mask)
    pm = np.zeros_like(pred_mask)
    pm[rows] = pred_mask[rows]
    inter = np.count_nonzero((pm > 0) & (gt_mask > 0))
    union = np.count_nonzero((pm > 0) | (gt_mask > 0))
    return inter / union if union else 0.0


def _f(row, k):
    v = row.get(k, "")
    return float(v) if v not in ("", None) else None


def score_frame(pred_row, gt, bev_w, bev_h, p: EvalParams):
    out = {"tp": 0, "fp": 0, "fn": 0}
    for side in ("left", "right"):
        valid = pred_row is not None and pred_row.get(f"{side}_valid") == "1"
        pm = None
        if valid:
            a, b, c = (_f(pred_row, f"{side}_{k}") for k in "abc")
            if None in (a, b, c):
                valid = False
            else:
                pm = geo.render_poly2(a, b, c, bev_w, bev_h, p.line_width_px)
        g = gt[side]
        iou = side_iou(pm, g) if (valid and g is not None) else None
        hit = iou is not None and iou >= p.iou_threshold
        out[f"gt_{side}"] = int(g is not None)
        out[f"pred_{side}"] = int(valid)
        out[f"iou_{side}"] = "" if iou is None else round(iou, 6)
        out["tp"] += int(hit)
        out["fp"] += int(valid and not hit)
        out["fn"] += int(g is not None and not hit)
    out["frame_ok"] = int(out["fp"] == 0 and out["fn"] == 0)
    return out


def summarize(frames, p: EvalParams, paired=None):
    c = np.array([[f["tp"], f["fp"], f["fn"]] for f in frames], dtype=np.int64).reshape(-1, 3)
    tp, fp, fn = (int(x) for x in c.sum(axis=0)) if len(c) else (0, 0, 0)
    P, R, F = stats.prf(tp, fp, fn)
    status = {}
    for f in frames:
        status[f["status"]] = status.get(f["status"], 0) + 1
    s = {"frames": len(frames), "tp": tp, "fp": fp, "fn": fn,
         "precision": P, "recall": R, "f1": F,
         "precision_ci": stats.wilson(tp, tp + fp), "recall_ci": stats.wilson(tp, tp + fn),
         "frame_ok": int(sum(f["frame_ok"] for f in frames)),
         "status_counts": status,
         "low_confidence_rate": status.get("low_confidence", 0) / len(frames) if frames else float("nan")}
    pc = None
    if paired is not None:
        pc = np.array([[f["tp"], f["fp"], f["fn"]] for f in paired], dtype=np.int64).reshape(-1, 3)
    s.update(stats.bootstrap_f1(c, p.bootstrap, p.seed, pc))
    if paired is not None:
        b = sum(1 for x, y in zip(frames, paired) if x["frame_ok"] and not y["frame_ok"])
        d = sum(1 for x, y in zip(frames, paired) if y["frame_ok"] and not x["frame_ok"])
        s["mcnemar"] = {"this_only_ok": b, "other_only_ok": d, "p_exact": stats.mcnemar_exact(b, d)}
    return s


def read_predictions(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


def write_per_frame(path, rows):
    keys = ["condition", "subset", "group", "key", "status", "gt_left", "gt_right", "pred_left",
            "pred_right", "iou_left", "iou_right", "tp", "fp", "fn", "frame_ok"]
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})


def params_dict(p: EvalParams):
    return asdict(p)


def dump_json(path, obj):
    with open(path, "w") as fh:
        json.dump(obj, fh, indent=2, default=float)
