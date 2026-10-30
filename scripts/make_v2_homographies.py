#!/usr/bin/env python3
"""v2 test homographies: the registered v1 calibration with the ROI start moved
to 0.5 m beyond the hood edge (docs/EVAL_PROTOCOL_V2.md, section 3).

Inputs are only the v1 calibration record (calibration/calibration_frames.json:
clicked rectangle, 3.75 m x 15 m) and the hood rows fixed in v1
(calibration/README.md). No test frame is used. The ground distance of the hood
row at the rectangle's centre column gives roi_near_m = Y(hood) + 0.5 m
(Y = 0 at the rectangle's near edge, negative towards the camera).

  python3 scripts/make_v2_homographies.py --culane_root /path/to/CULane
"""
import argparse, json, subprocess, sys
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from blsf_eval import geometry as geo  # noqa: E402

HOOD_ROWS = {"driver_37_30frame": 395, "driver_100_30frame": 440, "driver_193_90frame": 400}  # v1 README
MARGIN_M = 0.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--culane_root", required=True, help="for the calibration frames (previews only)")
    ap.add_argument("--out_dir", default=str(REPO / "calibration" / "v2"))
    a = ap.parse_args()
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    rec = json.loads((REPO / "calibration" / "calibration_frames.json").read_text())
    log = {}
    for drv, r in rec.items():
        pts = [tuple(float(v) for v in p.split(",")) for p in r["points"].split(";")]
        G = geo.ground_homography(pts, 3.75, 15.0)
        cx = 0.5 * (pts[2][0] + pts[3][0])
        g = G @ np.array([cx, HOOD_ROWS[drv], 1.0])
        y_hood = g[1] / g[2]
        near = round(float(y_hood) + MARGIN_M, 3)
        dst = out / f"culane_{drv}.yml"
        subprocess.run([sys.executable, str(HERE / "make_homography.py"), "--image", str(Path(a.culane_root) / r["key"]),
                        "--points", r["points"], "--rect_w_m", "3.75", "--rect_l_m", "15", "--roi_near_m", str(near),
                        "--out", str(dst), "--preview", str(out / f"culane_{drv}.png")], check=True)
        log[drv] = {"hood_row": HOOD_ROWS[drv], "y_hood_m": round(float(y_hood), 3), "roi_near_m": near}
        print(drv, log[drv])
    (out / "v2_roi.json").write_text(json.dumps(log, indent=1) + "\n")


if __name__ == "__main__":
    main()
