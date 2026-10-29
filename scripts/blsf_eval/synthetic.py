"""Synthetic CULane-style frames rendered from a known pinhole camera.

Used for tests and for the pre-registration sensitivity check only; never for
reported results. Ground frame: X right, Y forward (metres).
"""
from __future__ import annotations

import math
import cv2
import numpy as np

from . import geometry as geo

W, H = 1640, 590
PPM, XMIN, YMAX = 40.0, -12.0, 80.0  # ground map: 40 px per metre
F, CX, CY, CAM_H, PITCH = 1000.0, 820.0, 230.0, 1.5, 3.0
LANES = ((-5.625, False), (-1.875, False), (1.875, True), (5.625, False))
CALIB_RECT = [(-1.875, 21), (1.875, 21), (1.875, 6), (-1.875, 6)]  # TL, TR, BR, BL; 3.75 m x 15 m


def camera(f=F, cx=CX, cy=CY, h=CAM_H, pitch_deg=PITCH):
    """Ground -> image homography of a pinhole camera at height h, pitched down."""
    s, c = math.sin(math.radians(pitch_deg)), math.cos(math.radians(pitch_deg))
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1.0]])
    M = np.array([[1, 0, 0], [0, -s, c * h], [0, c, s * h]])
    return K @ M


def lane_x(x0, y, k):
    return x0 + k * max(0.0, y - 6.0) ** 2


def render(Hg, k, seed, dash_on=2.0, dash_off=4.0, stripes=False, blobs=10):
    """Return (BGR image, GT lanes as image points). k: curvature coefficient."""
    rng = np.random.default_rng(seed)
    gm = np.full((int((YMAX - 2) * PPM), int(24 * PPM)), 70, np.uint8)
    gm = np.clip(gm + rng.normal(0, 8, gm.shape), 0, 255).astype(np.uint8)
    to_px = lambda X, Y: (int(round((X - XMIN) * PPM)), int(round((YMAX - Y) * PPM)))
    for x0, dashed in LANES:
        ys = np.arange(2.0, YMAX, 0.05)
        for y0, y1 in zip(ys[:-1], ys[1:]):
            if dashed and ((y0 - 6.0) % (dash_on + dash_off)) >= dash_on:
                continue
            cv2.line(gm, to_px(lane_x(x0, y0, k), y0), to_px(lane_x(x0, y1, k), y1), 225, 6)
    for _ in range(blobs):  # bright blobs (reflections)
        c = (int(rng.integers(0, gm.shape[1])), int(rng.integers(0, gm.shape[0])))
        cv2.ellipse(gm, c, (int(rng.integers(20, 80)), int(rng.integers(5, 30))), float(rng.integers(0, 180)),
                    0, 360, int(rng.integers(150, 230)), -1)
    if stripes:  # crosswalk-like horizontal bars between 9 and 13 m
        for y in np.arange(9.0, 13.0, 0.9):
            cv2.rectangle(gm, to_px(-3.5, y + 0.45), to_px(3.5, y), 230, -1)
    T = np.array([[1 / PPM, 0, XMIN], [0, -1 / PPM, YMAX], [0, 0, 1.0]])
    img = cv2.warpPerspective(gm, Hg @ T, (W, H), flags=cv2.INTER_LINEAR, borderValue=40)
    horizon = int(math.ceil(CY - F * math.tan(math.radians(PITCH)))) + 3
    img[:horizon] = 40
    gt = []
    for x0, _ in LANES:
        pts = geo.warp_points(Hg, [(lane_x(x0, y, k), y) for y in np.arange(4.0, 60.0, 0.5)])
        pts = [p for p in pts if 0 <= p[0] < W and horizon <= p[1] < H]
        if len(pts) >= 2:
            gt.append(pts)
    return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR), gt
