"""End-to-end check of scripts/run_experiment.py on a rendered CULane-style dataset.

Frames are rendered from a known pinhole camera over a metric ground plane, so
the calibration rectangle and the ground truth are exact. Needs the built
binary (BLSF_BINARY or build/blsf_lane[.exe]); skipped otherwise.
"""
import json, os, pathlib, subprocess, sys, tempfile, unittest
import cv2
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from blsf_eval import geometry as geo  # noqa: E402
from blsf_eval.synthetic import camera, render, CALIB_RECT  # noqa: E402



def binary():
    env = os.environ.get("BLSF_BINARY")
    if env:
        return pathlib.Path(env)
    for n in ("blsf_lane", "blsf_lane.exe"):
        p = REPO / "build" / n
        if p.exists():
            return p
    return None


class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bin = binary()
        if cls.bin is None:
            raise unittest.SkipTest("built blsf_lane not found")

    def test_run_experiment_end_to_end(self):
        Hg = camera()
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d)
            root = d / "CULane"
            lists = {"straight": [], "curve": []}
            for i in range(8):
                sub = "straight" if i < 5 else "curve"
                k = 0.0 if sub == "straight" else 0.012
                img, gt = render(Hg, k, i, stripes=(i in (2, 6)))
                rel = f"driver_t_30frame/clip{i // 4}.MP4/{i:05d}.jpg"
                (root / rel).parent.mkdir(parents=True, exist_ok=True)
                cv2.imwrite(str(root / rel), img)
                (root / rel).with_suffix(".lines.txt").write_text(
                    "\n".join(" ".join(f"{x:.3f} {y:.3f}" for x, y in lane) for lane in gt) + "\n")
                lists[sub].append("/" + rel)
            (root / "list").mkdir()
            for sub, rows in lists.items():
                (root / "list" / f"{sub}.txt").write_text("\n".join(rows) + "\n")
            calib = lists["straight"][0]
            rect = geo.warp_points(Hg, CALIB_RECT)
            hom = d / "driver_t.yml"
            pts = ";".join(f"{x:.4f},{y:.4f}" for x, y in rect)
            subprocess.run([sys.executable, str(REPO / "scripts/make_homography.py"), "--image",
                            str(root / calib.lstrip("/")), "--points", pts, "--rect_w_m", "3.75",
                            "--rect_l_m", "15", "--out", str(hom), "--preview", str(d / "prev.png")],
                           check=True, capture_output=True)
            spec = {"name": "synthetic", "dataset": "culane", "root": str(root),
                    "subsets": {"straight": "list/straight.txt", "curve": "list/curve.txt"},
                    "exclude": [calib], "homographies": {"driver_t_30frame": str(hom)},
                    "conditions": {"with_blsf": "configs/paper_nominal.yaml",
                                   "without_blsf": "configs/paper_nominal_ablation_no_blsf.yaml"},
                    "eval": {"bootstrap": 200}}
            sp = d / "spec.json"
            sp.write_text(json.dumps(spec))
            work = d / "work"
            r = subprocess.run([sys.executable, str(REPO / "scripts/run_experiment.py"), "--spec", str(sp),
                                "--binary", str(self.bin), "--work_dir", str(work)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            s = json.loads((work / "results/summary.json").read_text())
            rows = (work / "results/per_frame.csv").read_text().strip().split("\n")
            self.assertEqual(len(rows) - 1, 2 * 7)  # calibration frame excluded, both conditions
            st = s["subsets"]["straight"]["with_blsf"]
            self.assertEqual(st["frames"], 4)
            self.assertGreaterEqual(st["f1"], 0.85, json.dumps(s, indent=1))
            self.assertIn("delta_f1_ci", s["subsets"]["all"]["with_blsf"])
            m = json.loads((work / "experiment_manifest.json").read_text())
            self.assertFalse(m["dry_run"])
            print("\n" + (work / "results/summary.md").read_text())

            bad = dict(spec, conditions={"with_blsf": "configs/default.yaml",
                                         "without_blsf": "configs/ablation_no_blsf.yaml"})
            sp.write_text(json.dumps(bad))
            r = subprocess.run([sys.executable, str(REPO / "scripts/run_experiment.py"), "--spec", str(sp),
                                "--binary", str(self.bin), "--work_dir", str(d / "work2")],
                               capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn("homography", r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
