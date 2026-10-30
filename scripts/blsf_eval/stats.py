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


def bootstrap_f1(counts, iters, seed, paired_counts=None, chunk=50):
    """Frame-level bootstrap of F1 (and of F1 difference when paired_counts given).

    counts: (n_frames, 3) per-frame tp, fp, fn.  Returns dict with 95% percentile CIs.
    Resamples are drawn in chunks of rows from one generator, which yields the same
    index stream as drawing all iters x n_frames at once but bounds memory.
    """
    counts = np.asarray(counts, dtype=np.int64)
    n = len(counts)
    rng = np.random.default_rng(seed)
    out = {}
    if n == 0:
        return {"f1_ci": [float("nan")] * 2}
    pc = None
    if paired_counts is not None:
        pc = np.asarray(paired_counts, dtype=np.int64)
        if pc.shape != counts.shape:
            raise ValueError("paired counts must cover the same frames")
    f_all, g_all = [], []
    done = 0
    while done < iters:
        k = min(chunk, iters - done)
        idx = rng.integers(0, n, size=(k, n))
        f_all.append(f1_from_counts(counts[idx].sum(axis=1)))
        if pc is not None:
            g_all.append(f1_from_counts(pc[idx].sum(axis=1)))
        done += k
    f = np.concatenate(f_all)
    out["f1_ci"] = [float(np.percentile(f, 2.5)), float(np.percentile(f, 97.5))]
    if pc is not None:
        d = f - np.concatenate(g_all)
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


def cluster_bootstrap(counts, clusters, iters, seed, ref="with_blsf"):
    """Paired cluster bootstrap of pooled P, R, F1 and of F1 differences.

    counts: {condition: (n_frames, 3) per-frame tp, fp, fn}, all over the same
    frames in the same order; clusters: (n_frames,) cluster id per frame (e.g.
    the source video clip). Each resample draws clusters with replacement; the
    same drawn clusters are used for every condition, tp/fp/fn are re-summed
    and pooled P, R, F1 recomputed. Returns 95 % percentile intervals and, for
    every condition other than ref, the interval of F1(ref) - F1(condition).
    """
    ids, inv = np.unique(np.asarray(clusters), return_inverse=True)
    k = len(ids)
    sums = {}
    for c, a in counts.items():
        a = np.asarray(a, dtype=np.int64).reshape(-1, 3)
        if len(a) != len(inv):
            raise ValueError("all conditions must cover the same frames")
        s = np.zeros((k, 3), dtype=np.int64)
        np.add.at(s, inv, a)
        sums[c] = s
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, k, size=(iters, k))
    out = {"clusters": int(k), "iters": int(iters), "seed": int(seed), "conditions": {}, "differences": {}}
    f1 = {}
    for c, s in sums.items():
        t = s[idx].sum(axis=1)
        tp, fp, fn = t[:, 0], t[:, 1], t[:, 2]
        with np.errstate(invalid="ignore", divide="ignore"):
            P = np.where(tp + fp > 0, tp / np.maximum(tp + fp, 1), 0.0)
            R = np.where(tp + fn > 0, tp / np.maximum(tp + fn, 1), 0.0)
        f1[c] = f1_from_counts(t)
        pct = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
        out["conditions"][c] = {"precision_ci": pct(P), "recall_ci": pct(R), "f1_ci": pct(f1[c])}
    if ref in f1:
        for c in f1:
            if c == ref:
                continue
            d = f1[ref] - f1[c]
            out["differences"][f"{ref} - {c}"] = {"delta_f1_ci": [float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))],
                                                 "p_delta_le_0": float(np.mean(d <= 0))}
    return out
