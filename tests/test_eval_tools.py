import math, pathlib, sys, tempfile, unittest
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from blsf_eval import geometry as geo, stats, evaluate as ev  # noqa: E402
from blsf_eval.synthetic import camera  # noqa: E402


def project(Hg2i, XY):
    return geo.warp_points(Hg2i, XY)


class Geometry(unittest.TestCase):
    def test_rectangle_maps_to_roi(self):
        Hg = camera()
        rect = [(-1.875, 21), (1.875, 21), (1.875, 6), (-1.875, 6)]
        pts = project(Hg, rect)
        H, sx, sy = geo.build_bev_homography(pts, 3.75, 15, 7.5, 10, 0, 225, 300)
        self.assertAlmostEqual(sx, 30.0)
        self.assertAlmostEqual(sy, 30.0)
        # ego boundaries at X=+-1.875 -> u = 112.5 -+ 56.25; Y=6 -> v=300, Y=16 -> v=0
        out = geo.warp_points(H, project(Hg, [(-1.875, 6), (1.875, 16), (0, 11)]))
        np.testing.assert_allclose(out, [[56.25, 300], [168.75, 0], [112.5, 150]], atol=1e-6)

    def test_points_behind_camera_are_nan(self):
        H = np.array([[1, 0, 0], [0, 1, 0], [0, 1, 0.0]])
        self.assertTrue(np.isnan(geo.warp_points(H, [(0, -5)])).all())

    def test_homography_yml_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "h.yml"
            geo.save_homography_yml(p, np.eye(3), 225, 300, {"rect_w_m": 3.75, "note": "x"})
            H, w, h = geo.load_homography_yml(p)
            self.assertEqual((w, h), (225, 300))
            np.testing.assert_allclose(H, np.eye(3))


class Stats(unittest.TestCase):
    def test_wilson_reference(self):
        lo, hi = stats.wilson(282, 297)  # p=0.95 example from the article
        self.assertAlmostEqual(lo, 0.9183, places=3)
        self.assertAlmostEqual(hi, 0.9696, places=3)

    def test_mcnemar(self):
        self.assertEqual(stats.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(stats.mcnemar_exact(0, 5), 0.0625)
        self.assertAlmostEqual(stats.mcnemar_exact(3, 3), 1.0)

    def test_bootstrap_paired(self):
        c = np.array([[2, 0, 0]] * 50)
        o = np.array([[1, 1, 1]] * 50)
        r = stats.bootstrap_f1(c, 200, 1, o)
        self.assertEqual(r["f1_ci"], [1.0, 1.0])
        self.assertAlmostEqual(r["delta_f1_ci"][0], 0.5)


class Scoring(unittest.TestCase):
    P = ev.EvalParams(line_width_px=15, iou_threshold=0.5, min_gt_rows=100)

    def gt(self, xl=60, xr=165):
        lanes = [[(xl, 299), (xl, 0)], [(xr, 299), (xr, 0)], [(5, 299), (5, 0)]]
        return ev.gt_ego_lanes(lanes, np.eye(3), 225, 300, self.P)

    def row(self, l=None, r=None, status="ok"):
        d = {"status": status, "left_valid": "0", "right_valid": "0"}
        for side, c in (("left", l), ("right", r)):
            if c is not None:
                d.update({f"{side}_valid": "1", f"{side}_a": "0", f"{side}_b": "0", f"{side}_c": str(c)})
        return d

    def test_ego_selection_ignores_outer_lane(self):
        g = self.gt()
        self.assertEqual(int(np.flatnonzero(g["left"][299]).mean()), 60)

    def test_hits_misses_and_rejection(self):
        g = self.gt()
        self.assertEqual(ev.score_frame(self.row(61, 164), g, 225, 300, self.P)["tp"], 2)
        s = ev.score_frame(self.row(61, 100), g, 225, 300, self.P)
        self.assertEqual((s["tp"], s["fp"], s["fn"]), (1, 1, 1))
        s = ev.score_frame(self.row(status="low_confidence"), g, 225, 300, self.P)
        self.assertEqual((s["tp"], s["fp"], s["fn"], s["frame_ok"]), (0, 0, 2, 0))
        none = {"left": None, "right": None}
        s = ev.score_frame(self.row(60, None), none, 225, 300, self.P)
        self.assertEqual((s["fp"], s["fn"]), (1, 0))

    def test_short_gt_lane_ignored(self):
        g = ev.gt_ego_lanes([[(60, 299), (60, 250)]], np.eye(3), 225, 300, self.P)
        self.assertIsNone(g["left"])


if __name__ == "__main__":
    unittest.main()
