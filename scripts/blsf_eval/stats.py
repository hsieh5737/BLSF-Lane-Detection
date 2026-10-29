"""Interval estimates and paired tests used by the protocol."""
from __future__ import annotations

import math
import numpy as np

Z95 = 1.959963984540054


def wilson(k: int, n: int, z: float = Z95):
    if n <= 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return p, r, f


def f1_from_counts(c):
    """c: array (..., 3) of tp, fp, fn summed over frames."""
    tp, fp, fn = c[..., 0], c[..., 1], c[..., 2]
    denom = 2 * tp + fp + fn
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(denom > 0, 2 * tp / np.maximum(denom, 1), 0.0)


def bootstrap_f1(counts, iters, seed, paired_counts=None):
    """Frame-level bootstrap of F1 (and of F1 difference when paired_counts given).

    counts: (n_frames, 3) per-frame tp, fp, fn.  Returns dict with 95% percentile CIs.
    """
    counts = np.asarray(counts, dtype=np.int64)
    n = len(counts)
    rng = np.random.default_rng(seed)
    out = {}
    if n == 0:
        return {"f1_ci": [float("nan")] * 2}
    idx = rng.integers(0, n, size=(iters, n))
    f = f1_from_counts(counts[idx].sum(axis=1))
    out["f1_ci"] = [float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))]
    if paired_counts is not None:
        pc = np.asarray(paired_counts, dtype=np.int64)
        if pc.shape != counts.shape:
            raise ValueError("paired counts must cover the same frames")
        g = f1_from_counts(pc[idx].sum(axis=1))
        d = f - g
        out["delta_f1_ci"] = [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))]
        out["delta_f1_p_le_0"] = float(np.mean(d <= 0))
    return out


def mcnemar_exact(b: int, c: int):
    """Two-sided exact McNemar test on discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    logs = [math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1) - n * math.log(2)
            for i in range(k + 1)]
    m = max(logs)
    tail = math.exp(m) * sum(math.exp(x - m) for x in logs)
    return min(1.0, 2 * tail)
