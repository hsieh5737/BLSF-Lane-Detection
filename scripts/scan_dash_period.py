#!/usr/bin/env python3
"""Find CULane calibration frames that show one full dash period on an ego boundary.

For frames of one test folder taken from NON-evaluated lists, the two ego
boundaries are fitted as straight lines from the official annotation (rows
280-470); their intersection is the vanishing row v_h. Brightness is sampled
along each boundary above the hood row; white runs are dashes. A frame
qualifies when the far end and near end of one dash and the far end of the
next dash are visible. Because ground distance is affine in u = 1/(v - v_h)
for a flat road and a pinhole camera, the dash fraction
(u_far1 - u_near1) / (u_far1 - u_far2) is invariant; 0.40 indicates the
6 m + 9 m pattern (15 m period), 0.33 the 2 m + 4 m pattern.
Candidates are then checked visually before one is used for make_homography.py.

  python3 scripts/scan_dash_period.py --root CULane --driver driver_193_90frame \
     --hood_row 400 --out scan.csv
"""
import argparse, csv, pathlib
import cv2
import numpy as np

LISTS = ["test1_crowd", "test3_shadow", "test5_arrow", "test7_cross"]  # not evaluated


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--driver", required=True)
    ap.add_argument("--hood_row", type=int, required=True)
    ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    root = pathlib.Path(a.root)
    keys = []
    for lst in LISTS:
        keys += [k.lstrip("/") for k in (root / "list/test_split" / f"{lst}.txt").read_text().split()
                 if k.lstrip("/").startswith(a.driver)]
    keys = sorted(set(keys))[::a.step]
    with open(a.out, "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["driver", "key", "status", "v_h", "side", "far1", "near1", "far2", "fraction",
                     "left_m", "left_b", "right_m", "right_b"])
        for key in keys:
            lanes = [np.array([float(t) for t in l.split()]).reshape(-1, 2)
                     for l in (root / key).with_suffix(".lines.txt").read_text().splitlines() if len(l.split()) >= 4]
            fits = []
            for L in lanes:
                sel = L[(L[:, 1] >= 280) & (L[:, 1] <= 470)]
                if len(sel) < 5:
                    continue
                m, b = np.polyfit(sel[:, 1], sel[:, 0], 1)
                r = np.sqrt(np.mean((m * sel[:, 1] + b - sel[:, 0]) ** 2))
                fits.append((m * 430 + b, m, b, r, sel[:, 1].min(), sel[:, 1].max()))
            Ls, Rs = [f for f in fits if f[0] < 820], [f for f in fits if f[0] >= 820]
            if not Ls or not Rs:
                wr.writerow([a.driver, key, "nolanes"]); continue
            l, r = max(Ls, key=lambda f: f[0]), min(Rs, key=lambda f: f[0])
            if l[3] > 3 or r[3] > 3 or abs(l[1] - r[1]) < 0.3:
                wr.writerow([a.driver, key, "curved"]); continue
            vh = (r[2] - l[2]) / (l[1] - r[1])
            g = cv2.imread(str(root / key), cv2.IMREAD_GRAYSCALE).astype(float)
            best = None
            for side, f in (("L", l), ("R", r)):
                y_lo, y_hi = int(max(vh + 20, f[4])), min(int(f[5]) - 3, a.hood_row)
                ys = np.arange(y_lo, y_hi)
                vals = []
                for y in ys:
                    x = f[1] * y + f[2]
                    hw = max(2, int(0.02 * (y - vh) * (abs(f[1]) + 1)))
                    s0, s1, b0, b1 = int(x - hw), int(x + hw) + 1, int(x - 5 * hw), int(x + 5 * hw) + 1
                    if b0 < 0 or b1 > g.shape[1]:
                        vals.append(np.nan); continue
                    peak = g[y, s0:s1].max()
                    vals.append(peak - np.median(g[y, b0:b1]) if peak > 140 else 0.0)
                v = np.array(vals)
                if np.isnan(v).any() or len(v) < 40:
                    continue
                on = v > 25
                runs, s = [], None
                for i, o in enumerate(on):
                    if o and s is None:
                        s = i
                    if (not o) and s is not None:
                        runs.append((s, i - 1)); s = None
                if s is not None:
                    runs.append((s, len(on) - 1))
                runs = [(ys[p], ys[q]) for p, q in runs if q - p >= 3]
                for i in range(len(runs) - 1):
                    f1, n1 = runs[i]; f2, _ = runs[i + 1]
                    if f1 <= y_lo + 1 or f2 - n1 < 3:
                        continue
                    u = lambda yy: 1.0 / (yy - vh)
                    cand = (side, f1, n1, f2, round((u(f1) - u(n1)) / (u(f1) - u(f2)), 3))
                    if best is None or (n1 - f1) > (best[2] - best[1]):
                        best = cand
            if best is None:
                wr.writerow([a.driver, key, "noperiod"]); continue
            wr.writerow([a.driver, key, "ok", round(vh, 1), *best, round(l[1], 4), round(l[2], 2),
                         round(r[1], 4), round(r[2], 2)])


if __name__ == "__main__":
    main()
