"""Checks for the secondary image-space metric (scripts/blsf_eval/evaluate_image.py)."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from blsf_eval import evaluate as ev, evaluate_image as ei, geometry as geo  # noqa: E402

H, W, HH = geo.load_homography_yml(Path(__file__).resolve().parents[1] / "calibration/v2/culane_driver_37_30frame.yml")
HI = ei.bev_to_image(H, W, HH)


def lane(x_bev):
    y = np.linspace(0, HH - 1, 40)
    return [tuple(p) for p in geo.warp_points(HI, np.stack([np.full_like(y, x_bev), y], 1))]


def row(xl, xr):
    return {"left_valid": "1", "left_a": "0", "left_b": "0", "left_c": str(xl),
            "right_valid": "1", "right_a": "0", "right_b": "0", "right_c": str(xr)}


class ImageMetric(unittest.TestCase):
    def test_perfect_and_shifted(self):
        lanes = [lane(75.0), lane(150.0)]
        pe, pi = ev.EvalParams(), ei.ImageEvalParams()
        f = ei.score_frame_image(row(75.0, 150.0), lanes, H, W, HH, pe, pi)
        self.assertEqual((f["tp"], f["fp"], f["fn"]), (2, 0, 0))
        self.assertGreater(f["img_iou_left"], 0.9)
        f = ei.score_frame_image(row(95.0, 170.0), lanes, H, W, HH, pe, pi)  # 1 m shift
        self.assertEqual((f["tp"], f["fp"], f["fn"]), (0, 2, 2))

    def test_missing_prediction_and_gt(self):
        pe, pi = ev.EvalParams(), ei.ImageEvalParams()
        r = row(75.0, 150.0); r["right_valid"] = "0"
        f = ei.score_frame_image(r, [lane(75.0)], H, W, HH, pe, pi)
        self.assertEqual((f["tp"], f["fp"], f["fn"]), (1, 0, 0))
        f = ei.score_frame_image(row(75.0, 150.0), [lane(75.0)], H, W, HH, pe, pi)
        self.assertEqual((f["tp"], f["fp"], f["fn"]), (1, 1, 0))


if __name__ == "__main__":
    unittest.main()
