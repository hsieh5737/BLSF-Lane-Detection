"""Checks for stats.cluster_bootstrap (primary intervals of protocol v2)."""
import sys, unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from blsf_eval import stats  # noqa: E402


class ClusterBootstrap(unittest.TestCase):
    def test_identical_conditions_give_zero_difference(self):
        rng = np.random.default_rng(0)
        c = rng.integers(0, 3, size=(200, 3))
        cl = np.repeat(np.arange(20), 10)
        r = stats.cluster_bootstrap({"with_blsf": c, "other": c.copy()}, cl, 300, 1)
        self.assertEqual(r["clusters"], 20)
        self.assertEqual(r["differences"]["with_blsf - other"]["delta_f1_ci"], [0.0, 0.0])

    def test_clusters_widen_interval(self):
        # frames inside a cluster are identical copies: the cluster interval must not be narrower
        rng = np.random.default_rng(1)
        base = rng.integers(0, 3, size=(30, 3))
        c = np.repeat(base, 20, axis=0)
        frame = stats.cluster_bootstrap({"with_blsf": c}, np.arange(len(c)), 500, 2)["conditions"]["with_blsf"]["f1_ci"]
        clip = stats.cluster_bootstrap({"with_blsf": c}, np.repeat(np.arange(30), 20), 500, 2)["conditions"]["with_blsf"]["f1_ci"]
        self.assertGreater(clip[1] - clip[0], frame[1] - frame[0])

    def test_mismatched_frames_rejected(self):
        with self.assertRaises(ValueError):
            stats.cluster_bootstrap({"with_blsf": np.zeros((5, 3)), "o": np.zeros((4, 3))}, np.arange(5), 10, 0)


if __name__ == "__main__":
    unittest.main()
