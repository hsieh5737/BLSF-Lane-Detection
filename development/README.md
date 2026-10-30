# Development log for the v2 correction (CULane train/val only)

This folder records how the v2 method (`configs/v2.yaml`) was developed after
the registered v1 evaluation (`results/culane_paper_nominal_20261030/`). It is
kept so that every design decision, including the rejected ones, can be
checked. No CULane test list was used in development. The only test-set
information that influenced v2 is the status count of the registered v1 run
(about half of all test frames ended as `no_peaks` in both conditions), which
motivated the work on initialisation.

## Data

- Validation: all 9,675 frames of `list/val.txt` (driver_23_30frame).
- Training sample: every 10th frame of `list/train.txt`
  (`lists/dev_train_sample.txt`); of these, the driver_161_90frame and
  driver_182_30frame frames (3,602) form subset `tr`.
- Tuning subsets: `val3` = every 3rd validation frame (3,225) and `tr`.
- Held-out confirmation: `valh` = the other 6,450 validation frames. It was
  scored three times (for the v2, v3 and v4 candidates below), so it is a
  confirmation set, not an untouched test set. The CULane test lists remain
  the only data never used before the registered v2 run.

## Calibration of the development drivers (`calibration/`)

The dev folders have no clicked calibration. A flat-road pinhole model was
fitted on training frames: vanishing row and column from the annotated ego
boundaries of straight-road frames (`scripts/vp_scan.py`), lateral scale from
the boundary slopes (3.75 m lane), and the longitudinal constant
k = f * h_cam from dash periods found by `scripts/scan_dash_period.py --list`
(mode of the plausible values: driver_23 577, driver_182 613; driver_161 had
too few dashes, 565 was taken from the median focal length implied by the
three registered test calibrations). The ROI is the same 11.25 m x 15 m on
225 x 300 px; `h2` starts 2 m beyond the hood edge (similar to the v1 test
calibration), `h05` 0.5 m beyond it. Check on annotated straight frames:
median lane width 3.31 / 3.58 / 3.59 m and median boundary angle about 1 deg,
comparable with the v1 test calibration QA. Per-clip vanishing rows vary by
about +/-6 px (5-95 %), so one homography per driver is adequate.

## Metrics

Primary: the registered v1 BEV ego-lane metric (10 px = 0.5 m, IoU >= 0.5).
A lateral shift of 0.3 m already fails it (tolerance about 0.17 m).
Secondary: CULane-style image-space IoU (30 px on 1640 x 590, IoU >= 0.5)
for the same two ego lanes inside the BEV ROI region
(`scripts/blsf_eval/evaluate_image.py`). Both were fixed before v2 tuning.

## Steps (BEV F1 on val3 / tr; full table in `dev_results_all.csv`)

| Step | With BLSF | Without BLSF | Decision |
|---|---|---|---|
| v1 settings, `h2` | 0.120 / 0.134 | 0.134 / 0.155 | baseline |
| BLSF decision by votes per degree only | 0.160 / 0.166 | - | kept |
| whole-BEV histogram, sides tracked separately (no density) | 0.155 / 0.193 | 0.171 / 0.194 | kept |
| both of the above | 0.199 / 0.232 | - | |
| + peak pair width 2.5-5 m | 0.212 / 0.233 | - | later removed |
| + RANSAC refit, curvature bound (R >= 30 m) | 0.252 / 0.268 | 0.206 / 0.226 | kept |
| Tg = 25 (paper 15) | 0.237 / 0.203 | 0.199 / 0.186 | rejected (Tg 35 worse) |
| ROI start 0.5 m beyond hood (`h05`) | 0.289 / 0.291 | 0.236 / 0.249 | kept |
| grid: curvature R >= 83 m, margin 12, min peak 12 | 0.374 / 0.337 | - | kept |
| margin 8, min peak 8, max offset 95, inlier 2.5, minpix 8 | no consistent gain | - | rejected |
| straight-line refit for short support (v2 candidate) | 0.383 / 0.342 | - | kept |
| no initial peak within 0.9 m of centre | 0.399 / 0.364 | - | kept |
| pair check + joint refit + inlier-fraction acceptance (v3) | 0.419 / 0.377 | 0.370 / 0.332 | |
| min peak 8, centre 1.25 m, minpix 20 | no gain | - | rejected |
| Gaussian pre-blur 3 / 5 px | 0.445 / 0.350, 0.421 / 0.313 | - | rejected (helps one driver only) |

Rejected without a table row: inferring the missing side from a lane-width
offset (about 12 % of inferred sides correct).

## Leave-one-out ablation of v3 (val3 / tr, v3 = 0.419 / 0.377)

| Removed | BEV F1 | Decision |
|---|---|---|
| votes-per-degree decision (published Eq. 6 instead) | 0.340 / 0.318 | core |
| separate sides (v1: both peaks required) | 0.351 / 0.298 | keep |
| whole-BEV histogram (v1: lower half) | 0.382 / 0.328 | keep |
| margin 12 (v1 21) | 0.373 / 0.358 | keep |
| ROI 0.5 m beyond hood (`h2` instead) | 0.371 / 0.348 | keep |
| inlier-fraction acceptance | 0.404 / 0.367 | keep |
| centre exclusion | 0.419 / 0.360 | keep |
| refit / curvature bound / straight refit | 0.410 / 0.370, 0.414 / 0.370, 0.414 / 0.372 | keep |
| nearest-to-expected peak selection | 0.418 / 0.375 | removed |
| peak pair width | 0.420 / 0.376 | removed |
| pair check + joint refit | 0.415 / 0.374 (image metric +0.015 / +0.009) | removed |

The simplified method is v4 = `configs/v2.yaml`.

## Final candidates on the held-out validation frames (`valh`, 6,450 frames)

| Method | BEV P / R / F1 | Image F1 |
|---|---|---|
| v1 with BLSF (`h2`) | 0.289 / 0.083 / 0.129 | 0.182 |
| v1 without BLSF (`h2`) | 0.195 / 0.108 / 0.139 | 0.224 |
| v3 with BLSF | 0.633 / 0.321 / 0.426 | 0.492 |
| **v4 with BLSF (`configs/v2.yaml`)** | 0.564 / 0.331 / **0.417** | **0.495** |
| v4 without BLSF | 0.454 / 0.320 / 0.375 | 0.460 |
| v4 with published Eq. (6) | 0.550 / 0.259 / 0.352 | 0.411 |

Frame bootstrap (1,000 resamples) of the paired difference for v3 on valh:
with - without +0.040 to +0.054 (BEV), +0.031 to +0.046 (image);
with - Eq. (6) +0.067 to +0.084 (BEV).

## Checks after the choice of v4 (no further change made)

- Per-strip band selection (2 or 3 BEV strips, same bands and rule):
  0.407 / 0.364 and 0.405 / 0.358, no gain on curved frames; not adopted.
- Curvature bound R >= 30 m instead of 83 m: -0.010 / -0.005 overall,
  +0.005 / +0.010 on curved frames; not adopted.
- Curved frames (GT |a| > 3e-4, about 150 per subset): v4 with 0.152 / 0.199,
  without 0.140 / 0.195.
- Dark frames (mean brightness < 50, 875 frames of `tr`): with 0.376
  (precision 0.66), without 0.360 (precision 0.52).

## Reproduction

`scripts/devrun.py` (paths at the top: dev data copy and this folder's
calibration), configurations in `configs/`, lists in `lists/`. CULane images
are not redistributed.
