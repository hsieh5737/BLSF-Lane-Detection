# Registered evaluation v2: CULane test set (docs/EVAL_PROTOCOL_V2.md)

- Registration: commit `9acbb780bd37eacce159f03d6c150b2431315396`
  (2026-10-30 09:40:57 UTC); `git archive` SHA-256
  `f2991afeb4cb3a46d8dacaa16f8fc18c61f3d0b1f7b20d231464f2afc8e7f074`.
- Runs: 2026-10-30 10:50-11:40 UTC, binary built from that archive (SHA-256
  of `blsf_lane` in `run_manifest.json`), 3 conditions x 17,558 frames, 78
  runs, all with exit code 0. Run outputs archived in `work_v2_runs.tgz`
  (`runs_archive.sha256`); images are not redistributed.
- Scoring: 2026-10-30 11:42-11:47 UTC from the same archive (not a git
  checkout, hence `repository.commit: null` in `eval_manifest.json`), Python
  OpenCV 4.6.0. List hashes and the annotation set are identical to v1.
- Every listed frame is included; rejected and failed frames count as
  frames without a prediction.

## Primary result (BEV metric, pooled `all`, 17,558 frames, 380 clips)

| Condition | P | R | F1 | 95 % clip CI |
|---|---|---|---|---|
| with_blsf (`configs/v2.yaml`) | 0.745 | 0.447 | **0.559** | [0.521, 0.593] |
| without_blsf | 0.658 | 0.455 | 0.538 | [0.499, 0.573] |
| with_blsf_eq6 (published Eq. 6) | 0.727 | 0.414 | 0.527 | [0.490, 0.562] |

| Hypothesis (fixed sequence) | dF1 | 95 % clip CI | Decision |
|---|---|---|---|
| H1 with_blsf - without_blsf | +0.021 | [+0.015, +0.027] | supported |
| H2 with_blsf - with_blsf_eq6 | +0.032 | [+0.024, +0.041] | supported (H1 supported) |

## By subset (BEV metric, F1 and clip-level 95 % intervals; not tested)

| Subset (frames, clips) | with_blsf | without_blsf | eq6 | with - without | with - eq6 |
|---|---|---|---|---|---|
| dazzle (486, 48) | 0.292 | 0.297 | 0.256 | [-0.034, +0.029] | [+0.003, +0.062] |
| night (7,029, 61) | 0.477 | 0.440 | 0.419 | [+0.025, +0.046] | [+0.041, +0.078] |
| curve (422, 70) | 0.327 | 0.358 | 0.345 | [-0.057, -0.006] | [-0.045, +0.001] |
| normal (9,621, 315) | 0.626 | 0.614 | 0.606 | [+0.006, +0.018] | [+0.014, +0.027] |

BLSF raises precision in every subset except curve (0.580 vs 0.583) and
lowers recall slightly; on the curve subset it is worse than no BLSF
(dF1 -0.031). Low-confidence rejection: 9.8 % of all frames (night 15.8 %,
curve 13.7 %, dazzle 13.2 %, normal 5.0 %).

## Secondary metric (image space, pooled `all`)

F1 0.600 / 0.588 / 0.567; with - without +0.012 [+0.006, +0.017], with - eq6
+0.033 [+0.024, +0.041] (clip-level). Curve: 0.395 / 0.399 / 0.395.

## Descriptive (frame-level intervals and McNemar; not used for decisions)

See `summary.md` (first two tables). Frame-level intervals are narrower than
the clip-level ones because frames of a clip are correlated.

## Relation to v1

v1 (`results/culane_paper_nominal_20261030/`) pooled F1 was 0.290 with and
0.292 without BLSF. v2 uses a nearer ROI, so the two versions are scored
over different ground regions; the comparison is descriptive only.

## Deviation

The co-author was told of the freeze online before the run; the e-mail with
the commit and archive hash was sent at 10:54 UTC, about 3 minutes after the
runs started (10:50:39 UTC) and before any scoring (11:42 UTC).
