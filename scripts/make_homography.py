#!/usr/bin/env python3
"""Build a BEV homography from a clicked ground rectangle of known size.

Points are the image pixel corners of a real ground rectangle, in the order
far-left, far-right, near-right, near-left (TL, TR, BR, BL). For a straight lane
the rectangle can be the ego lane between its two boundary lines (width = lane
width) over one dash period (length = dash + gap). The BEV ROI defaults to a
3:4 ground area (11.25 m x 15 m: ego lane plus both neighbours, one
15 m dash period) on a 225x300 grid, i.e. 20 px/m on both axes, so a 15 cm
marking is ~3 px against the 9 px MLT window (see docs/EVAL_PROTOCOL.md).
Writes the homography plus the inputs used, and optionally a preview image.
"""
import argparse, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from blsf_eval import geometry as geo  # noqa: E402


def parse_points(s):
    pts = [tuple(float(v) for v in p.split(",")) for p in s.split(";")]
    if len(pts) != 4 or any(len(p) != 2 for p in pts):
        raise argparse.ArgumentTypeError("need 4 points 'x,y;x,y;x,y;x,y' (TL;TR;BR;BL)")
    return pts


def pick_points(img):
    """Click TL, TR, BR, BL; Backspace undoes, Enter accepts, Esc aborts."""
    pts, win = [], "click TL, TR, BR, BL of the ground rectangle (Enter=OK, Backspace=undo, Esc=quit)"
    cv2.namedWindow(win, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(win, lambda e, x, y, f, u: pts.append((float(x), float(y)))
                         if e == cv2.EVENT_LBUTTONDOWN and len(pts) < 4 else None)
    while True:
        show = img.copy()
        for i, (x, y) in enumerate(pts):
            cv2.circle(show, (int(x), int(y)), 4, (0, 255, 0), -1)
            cv2.putText(show, "TL TR BR BL".split()[i], (int(x) + 6, int(y) - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        if len(pts) > 1:
            cv2.polylines(show, [np.array(pts, np.int32)], len(pts) == 4, (0, 255, 0), 1)
        cv2.imshow(win, show)
        k = cv2.waitKey(30) & 0xFF
        if k == 27:
            raise SystemExit("aborted")
        if k == 8 and pts:
            pts.pop()
        if k in (10, 13) and len(pts) == 4:
            cv2.destroyWindow(win)
            print("points:", ";".join(f"{x:.1f},{y:.1f}" for x, y in pts))
            return pts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True, help="frame used for calibration (excluded from evaluation)")
    ap.add_argument("--points", type=parse_points, help="x,y;x,y;x,y;x,y (TL;TR;BR;BL)")
    ap.add_argument("--pick", action="store_true", help="click the 4 points in a window instead")
    ap.add_argument("--rect_w_m", type=float, required=True)
    ap.add_argument("--rect_l_m", type=float, required=True)
    ap.add_argument("--roi_w_m", type=float, default=11.25)
    ap.add_argument("--roi_l_m", type=float, default=15.0)
    ap.add_argument("--roi_near_m", type=float, default=0.0)
    ap.add_argument("--lateral_offset_m", type=float, default=0.0)
    ap.add_argument("--bev", default="225x300")
    ap.add_argument("--allow_anisotropic", action="store_true")
    ap.add_argument("--out", required=True)
    ap.add_argument("--preview")
    a = ap.parse_args()

    img = cv2.imread(a.image)
    if img is None:
        raise SystemExit(f"cannot read {a.image}")
    if a.points is None:
        if not a.pick:
            raise SystemExit("give --points or --pick")
        a.points = pick_points(img)
    bw, bh = (int(v) for v in a.bev.lower().split("x"))
    sx, sy = bw / a.roi_w_m, bh / a.roi_l_m
    if abs(sx / sy - 1) > 1e-9 and not a.allow_anisotropic:
        raise SystemExit(f"ROI {a.roi_w_m}x{a.roi_l_m} m on {bw}x{bh} px is anisotropic (sx/sy={sx/sy:.4f})")
    if abs(a.roi_w_m / a.roi_l_m - 0.75) > 1e-9:
        print(f"WARNING: ROI aspect {a.roi_w_m/a.roi_l_m:.4f} differs from the configured 3:4", file=sys.stderr)
    H, sx, sy = geo.build_bev_homography(a.points, a.rect_w_m, a.rect_l_m, a.roi_w_m, a.roi_l_m,
                                         a.roi_near_m, bw, bh, a.lateral_offset_m)
    meta = {"calibration_image": str(Path(a.image).as_posix()),
            "image_points_tl_tr_br_bl": np.array(a.points), "rect_w_m": a.rect_w_m, "rect_l_m": a.rect_l_m,
            "roi_w_m": a.roi_w_m, "roi_l_m": a.roi_l_m, "roi_near_m": a.roi_near_m,
            "lateral_offset_m": a.lateral_offset_m, "sx_px_per_m": sx, "sy_px_per_m": sy}
    geo.save_homography_yml(a.out, H, bw, bh, meta)
    print(f"wrote {a.out}: {bw}x{bh} px, sx={sx:.3f} px/m, sy={sy:.3f} px/m")
    if a.preview:
        bev = cv2.warpPerspective(img, H, (bw, bh))
        for m in range(1, int(a.roi_l_m) + 1):  # 1 m grid
            y = int(round(bh - m * sy))
            cv2.line(bev, (0, y), (bw - 1, y), (0, 255, 255) if m % 5 == 0 else (0, 120, 120), 1)
        for m in range(1, int(a.roi_w_m) + 1):
            x = int(round(m * sx))
            cv2.line(bev, (x, 0), (x, bh - 1), (0, 120, 120), 1)
        cv2.imwrite(a.preview, bev)
        print(f"preview {a.preview}: lane lines should be vertical and parallel")


if __name__ == "__main__":
    main()
