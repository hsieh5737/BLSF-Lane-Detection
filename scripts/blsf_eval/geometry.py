"""BEV geometry for the evaluation protocol.

Ground frame: X lateral (metres, right positive), Y forward (metres).
A calibration rectangle of known size is clicked in the image as
TL, TR, BR, BL (far-left, far-right, near-right, near-left); its near-left
corner is the ground origin.  The BEV ROI is a ground rectangle of width
roi_w_m and length roi_l_m, centred laterally on the calibration rectangle
(plus an optional offset) and starting roi_near_m beyond its near edge.
BEV pixels: u = (X - X0) * bev_w / roi_w_m, v = (Y_far - Y) * bev_h / roi_l_m.
"""
from __future__ import annotations

import numpy as np
import cv2


def ground_homography(image_pts, rect_w_m: float, rect_l_m: float) -> np.ndarray:
    """Image -> ground (metres) homography from the clicked rectangle."""
    src = np.asarray(image_pts, dtype=np.float64).reshape(4, 2)
    dst = np.array([[0.0, rect_l_m], [rect_w_m, rect_l_m], [rect_w_m, 0.0], [0.0, 0.0]])
    if rect_w_m <= 0 or rect_l_m <= 0:
        raise ValueError("calibration rectangle size must be positive")
    return homography_4pt(src, dst)


def homography_4pt(src, dst) -> np.ndarray:
    """Exact homography from four correspondences, solved in float64."""
    A, b = [], []
    for (x, y), (u, v) in zip(src, dst):
        A.append([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.append(u)
        A.append([0, 0, 0, x, y, 1, -v * x, -v * y]); b.append(v)
    A = np.array(A, dtype=np.float64)
    if abs(np.linalg.det(A)) < 1e-12:
        raise ValueError("degenerate calibration points (three collinear?)")
    h = np.linalg.solve(A, np.array(b, dtype=np.float64))
    return np.append(h, 1.0).reshape(3, 3)


def roi_to_pixels(rect_w_m, roi_w_m, roi_l_m, roi_near_m, bev_w, bev_h, lateral_offset_m=0.0):
    """Ground (metres) -> BEV pixel affine map as a 3x3 matrix."""
    if roi_w_m <= 0 or roi_l_m <= 0 or bev_w <= 0 or bev_h <= 0:
        raise ValueError("ROI and BEV sizes must be positive")
    x0 = rect_w_m / 2.0 + lateral_offset_m - roi_w_m / 2.0
    y_far = roi_near_m + roi_l_m
    sx = bev_w / roi_w_m
    sy = bev_h / roi_l_m
    return np.array([[sx, 0.0, -sx * x0], [0.0, -sy, sy * y_far], [0.0, 0.0, 1.0]])


def build_bev_homography(image_pts, rect_w_m, rect_l_m, roi_w_m, roi_l_m,
                         roi_near_m, bev_w, bev_h, lateral_offset_m=0.0):
    G = ground_homography(image_pts, rect_w_m, rect_l_m)
    S = roi_to_pixels(rect_w_m, roi_w_m, roi_l_m, roi_near_m, bev_w, bev_h, lateral_offset_m)
    H = S @ G
    return orient_homography(H, bev_w, bev_h), bev_w / roi_w_m, bev_h / roi_l_m


def orient_homography(H, bev_w, bev_h):
    """Scale H so that image points on the ground ahead map with w > 0.

    The near-centre BEV pixel is on the ground in front of the camera; the sign
    of its pre-image's homogeneous coordinate fixes the overall sign of H.
    """
    H = np.asarray(H, dtype=np.float64)
    c = (np.linalg.inv(H) @ np.array([bev_w / 2.0, bev_h - 1.0, 1.0]))[2]
    H = -H if c < 0 else H
    return H / np.abs(H).max()


def warp_points(H, pts) -> np.ndarray:
    pts = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
    if len(pts) == 0:
        return pts
    hom = np.hstack([pts, np.ones((len(pts), 1))]) @ H.T
    w = hom[:, 2:3]
    out = np.full_like(pts, np.nan)
    ok = w[:, 0] > 1e-9  # points in front of the camera only
    out[ok] = hom[ok, :2] / w[ok]
    return out


def save_homography_yml(path, H, bev_w, bev_h, meta: dict):
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_WRITE)
    if not fs.isOpened():
        raise OSError(f"cannot write {path}")
    fs.write("bev_w", int(bev_w))
    fs.write("bev_h", int(bev_h))
    fs.write("H", np.asarray(H, dtype=np.float64))
    for k, v in meta.items():
        if isinstance(v, (list, tuple, np.ndarray)):
            fs.write(k, np.asarray(v, dtype=np.float64))
        elif isinstance(v, str):
            fs.write(k, v)
        else:
            fs.write(k, float(v))
    fs.release()


def load_homography_yml(path):
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    if not fs.isOpened():
        raise OSError(f"cannot read {path}")
    w = int(fs.getNode("bev_w").real())
    h = int(fs.getNode("bev_h").real())
    H = fs.getNode("H").mat()
    fs.release()
    if H is None or H.shape != (3, 3) or w <= 0 or h <= 0:
        raise ValueError(f"invalid homography file {path}")
    return orient_homography(H, w, h), w, h


def _clamp(x):
    return np.clip(x, -1e4, 1e4)


def render_polyline(pts, bev_w, bev_h, width_px) -> np.ndarray:
    """0/255 mask of a polyline given in BEV pixel coordinates (NaNs split it)."""
    mask = np.zeros((bev_h, bev_w), np.uint8)
    pts = np.asarray(pts, dtype=np.float64).reshape(-1, 2)
    run = []
    def flush():
        if len(run) >= 2:
            arr = np.round(_clamp(np.array(run))).astype(np.int32).reshape(-1, 1, 2)
            cv2.polylines(mask, [arr], False, 255, int(width_px), cv2.LINE_8)
        run.clear()
    for p in pts:
        if np.all(np.isfinite(p)):
            run.append(p)
        else:
            flush()
    flush()
    return mask


def render_poly2(a, b, c, bev_w, bev_h, width_px) -> np.ndarray:
    """Mask of x = a*y^2 + b*y + c over all BEV rows (tracker output convention)."""
    y = np.arange(bev_h, dtype=np.float64)
    x = a * y * y + b * y + c
    return render_polyline(np.stack([x, y], axis=1), bev_w, bev_h, width_px)


def covered_rows(mask) -> np.ndarray:
    return np.flatnonzero(mask.any(axis=1))
