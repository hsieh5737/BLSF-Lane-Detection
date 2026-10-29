#!/usr/bin/env python3
"""Pre-registration sensitivity check on synthetic frames (never test data).

Renders fixed synthetic scenes (dash pattern, curvature, crosswalk clutter),
runs a configuration pair with optional single-key overrides, and scores the
frames with the protocol's evaluator. Used to justify settings that are not
given in the article before any real frame is evaluated.

Example:
  python3 scripts/synthetic_sensitivity.py --binary build/blsf_lane \
    --variant "proportional:peaks.min_peak_value=31" --variant "adopted:peaks.min_peak_value=12" \
    --out evidence/validation/synthetic_sensitivity.md
"""
import argparse, re, shutil, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import cv2  # noqa: E402
from blsf_eval import geometry as geo, evaluate as ev, synthetic as syn  # noqa: E402

SCENES = [  # (label, dash_on, dash_off, k, stripes)
    ("straight, 2/4 m dashes", 2, 4, 0.0, False),
    ("straight, 4/6 m dashes", 4, 6, 0.0, False),
    ("straight, 6/9 m dashes", 6, 9, 0.0, False),
    ("straight, 6/9 m, crosswalk", 6, 9, 0.0, True),
    ("right curve k=0.012, 2/4 m", 2, 4, 0.012, False),
    ("right curve k=0.012, 6/9 m", 6, 9, 0.012, False),
    ("left curve k=-0.008, 6/9 m, crosswalk", 6, 9, -0.008, True),
]


def override(text, dotted, value):
    section, key = dotted.split(".")
    pat = re.compile(rf"(^{section}:\n(?:[ ]+.*\n)*?[ ]+{key}:)[ ]*[^\n#]*", re.M)
    new, n = pat.subn(rf"\g<1> {value}", text)
    if n != 1:
        raise SystemExit(f"cannot override {dotted}")
    return new


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", required=True)
    ap.add_argument("--with_config", default=str(REPO / "configs/paper_nominal.yaml"))
    ap.add_argument("--without_config", default=str(REPO / "configs/paper_nominal_ablation_no_blsf.yaml"))
    ap.add_argument("--variant", action="append", default=[], help="label:section.key=value[,section.key=value]")
    ap.add_argument("--frames", type=int, default=16)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    variants = [("as configured", [])]
    for v in a.variant:
        label, spec = v.split(":", 1)
        variants.append((label, [s.split("=", 1) for s in spec.split(",")]))
    P = ev.EvalParams()
    Hg = syn.camera()
    rect = geo.warp_points(Hg, syn.CALIB_RECT)
    H, _, _ = geo.build_bev_homography(rect, 3.75, 15, 11.25, 15, 0, 225, 300)
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        geo.save_homography_yml(d / "h.yml", H, 225, 300, {})
        scenes = {}
        for i, (label, on, off, k, st) in enumerate(SCENES):
            sd = d / f"scene{i}"
            sd.mkdir()
            gts = {}
            for j in range(a.frames):
                img, gt = syn.render(Hg, k, 1000 * i + j, on, off, stripes=st)
                cv2.imwrite(str(sd / f"f{j:02d}.png"), img)
                gts[f"f{j:02d}.png"] = ev.gt_ego_lanes(gt, H, 225, 300, P)
            scenes[label] = (sd, gts)
        header = "| Scene | " + " | ".join(f"{v[0]} with / without" for v in variants) + " |"
        lines = [f"Synthetic pre-registration check: {a.frames} frames per scene, BEV 225x300 on 11.25 x 15 m, "
                 f"F1 (ego lanes, IoU>={P.iou_threshold}, width {P.line_width_px} px).", "", header,
                 "|---|" + "---|" * len(variants)]
        for label, (sd, gts) in scenes.items():
            cells = []
            for vlabel, ovs in variants:
                pair = []
                for cfg in (a.with_config, a.without_config):
                    text = Path(cfg).read_text()
                    for key, val in ovs:
                        text = override(text, key, val)
                    c = d / "cfg.yaml"
                    c.write_text(text)
                    o = d / "out"
                    shutil.rmtree(o, ignore_errors=True)
                    subprocess.run([a.binary, "--config", str(c), "--input_dir", str(sd), "--homography",
                                    str(d / "h.yml"), "--output_dir", str(o), "--no_debug"],
                                   check=True, capture_output=True)
                    tp = fp = fn = 0
                    for row in ev.read_predictions(o / "predictions.csv"):
                        s = ev.score_frame(row, gts[re.split(r"[\\/]", row["image"])[-1]], 225, 300, P)
                        tp, fp, fn = tp + s["tp"], fp + s["fp"], fn + s["fn"]
                    pair.append(2 * tp / max(1, 2 * tp + fp + fn))
                cells.append(f"{pair[0]:.3f} / {pair[1]:.3f}")
            lines.append(f"| {label} | " + " | ".join(cells) + " |")
    Path(a.out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
