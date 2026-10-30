# Development log for the v2 correction (CULane train/val only)

This folder records how the v2 method (`configs/v2.yaml`) was developed after
the registered v1 evaluation (`results/culane_paper_nominal_20261030/`). It is
kept so that every design decision, including the rejected ones, can be
checked. No CULane test list was used to run or score any development
candidate.

Test-set information that did reach the development (the same disclosure as
section 0 of `docs/EVAL_PROTOCOL_V2.md`):

1. The summary of the registered v1 test run, in particular the status counts
   (about half of all test frames ended as `no_peaks` in both conditions),
   which motivated the work on initialisation.
2. The v1 calibration of the test camera folders (clicked rectangles and hood
   rows, from non-evaluated test lists): it fixes the v2 test homographies
   (`scripts/make_v2_homographies.py`), and the median focal length implied by
   the three v1 test calibrations was used for one development calibration
   constant (driver_161, below).

## Data

- Validation: all 9,675 frames of `list/val.txt` (driver_23_30frame).
- Training sample: every 10th frame of `list/train.txt`
  (`lists/dev_train_sample.txt`); of these, the driver_161_90frame and
  driver_182_30frame frames (3,602) form subset `tr`.
- Tuning subsets: `val3` = every 3rd validation frame (3,225) and `tr`.
- Development confirmation set: `valh` = the other 6,450 validation frames.
  It is interleaved with `val3` (same 54 video clips) and was scored for
  several candidates (v2, v3, v4, final), so it is not an independent
  held-out set. No test frame was run or scored with a development
  candidate; the test-set information that did reach the development is
  listed at the top of this file.

## Calibration of the development drivers (`calibration/`)

The dev folders have no clicked calibration. A flat-road pinhole model was
fitted on training frames: vanishing row and column from the annotated ego
boundaries of straight-road frames (`scripts/vp_scan.py`), lateral scale from
the boundary slopes, and a longitudinal constant from dash periods. Model and
units: an image row is v = v_h + k / Z for a ground point at distance Z (m),
with k = f * h_cam in px * m (f = focal length in pixels, h_cam = camera
height in m); a column is x = v_x + X * c * k / (W * Z), where c (no unit) is
the difference of the two boundary slopes dx/dv and W = 3.75 m, so that
h_cam = W / c. k was estimated from dash periods found by
`scripts/scan_dash_period.py --list` (mode of the plausible values):
driver_23 577 px * m (h_cam 1.33 m), driver_182 613 px * m (1.25 m).
driver_161 had too few usable dashes; its k = 565 px * m comes from the
median focal length of the three v1 test calibrations, f = 457 px (419, 457,
495 px for driver_37, driver_100, driver_193), times h_cam = 3.75 / 3.019 =
1.24 m (computed 567, entered as 565). Barrel distortion is ignored, so f is
an effective pinhole value for the central road region. The ROI is the same 11.25 m x 15 m on
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

The simplified method is v4; the final `configs/v2.yaml` is v4 with the two
revisions in the last section.

## Candidates on the development confirmation set (`valh`, 6,450 frames)

| Method | BEV P / R / F1 | Image F1 |
|---|---|---|
| v1 with BLSF (`h2`) | 0.289 / 0.083 / 0.129 | 0.182 |
| v1 without BLSF (`h2`) | 0.195 / 0.108 / 0.139 | 0.224 |
| v3 with BLSF | 0.633 / 0.321 / 0.426 | 0.492 |
| v4 with BLSF | 0.564 / 0.331 / 0.417 | 0.495 |
| v4 without BLSF | 0.454 / 0.320 / 0.375 | 0.460 |
| v4 with published Eq. (6) | 0.550 / 0.259 / 0.352 | 0.411 |

(Frame-level bootstrap intervals reported earlier for v3 are superseded by
the clip-level intervals below.)

## Checks after the choice of v4 (no further change made)

- Per-strip band selection (2 or 3 BEV strips, same bands and rule):
  0.407 / 0.364 and 0.405 / 0.358, no gain on curved frames; not adopted.
- Curvature bound R >= 30 m instead of 83 m: -0.010 / -0.005 overall,
  +0.005 / +0.010 on curved frames; not adopted.
- Curved frames (GT |a| > 3e-4, about 150 per subset): v4 with 0.152 / 0.199,
  without 0.140 / 0.195.
- Dark frames (mean brightness < 50, 875 frames of `tr`): with 0.376
  (precision 0.66), without 0.360 (precision 0.52).

## Revisions after co-author review (final `configs/v2.yaml`)

1. Confidence gate. With the votes-per-degree rule, v4 gated on the selected
   band's vote; the paper gates on max_k B_k. v2 now uses the paper's gate
   (`blsf.gate: "max"`). It changes 1-5 % of frames; BEV F1 val3 / tr
   0.413 / 0.372 (v4) -> 0.412 / 0.375.
2. Curvature bound (nominal limit on the fitted parabola; radius at
   20 px/m). Sensitivity, BEV F1 val3 / tr (curved frames val3 / tr):
   R >= 30 m 0.403 / 0.367 (0.157 / 0.209; measured with the v4 gate);
   R >= 50 m 0.409 / 0.373 (0.159 / 0.209); R >= 83 m 0.412 / 0.375
   (0.152 / 0.196); R >= 150 m 0.413 / 0.379 (0.142 / 0.196). Relative to the
   chosen 50 m setting, overall F1 changes by at most 0.006 over 30-150 m,
   and the looser bounds score higher on curved frames. The nominal limit
   R >= 50 m (`max_abs_a` 5e-4) was chosen from this development
   sensitivity.
3. ROI start beyond the hood edge (BEV F1 val3 / tr, with / without BLSF,
   R >= 83 m): 0.25 m 0.424 / 0.375, 0.383 / 0.323; 0.5 m 0.412 / 0.375,
   0.373 / 0.319; 1 m 0.403 / 0.366, 0.358 / 0.317; 2 m 0.368 / 0.348,
   0.325 / 0.307. Nearer is better; 0.5 m is kept because the hood rows were
   read by eye in v1 and 0.5 m leaves about 14 image rows between the ROI and
   the hood edge, against about 7 rows at 0.25 m.
4. Published rule vs votes per degree with everything else equal: v1
   pipeline 0.120 / 0.134 (Eq. 6) vs 0.160 / 0.166 (per degree); v4 pipeline
   0.342 / 0.316 (`v4sum`) vs 0.413 / 0.372; final pipeline 0.339 / 0.315 vs
   0.409 / 0.373.

Final configuration on the development confirmation set (`valh`):

| Condition | BEV P / R / F1 | Image F1 |
|---|---|---|
| with BLSF (`f_with` = `configs/v2.yaml`) | 0.546 / 0.331 / 0.412 | 0.494 |
| without BLSF (`f_without`) | 0.437 / 0.320 / 0.369 | 0.460 |
| with BLSF, published Eq. (6) (`f_eq6`) | 0.535 / 0.259 / 0.349 | 0.410 |

Paired bootstrap of the F1 difference, frame-level vs clip-level resampling
(2,000 resamples; `scripts/clusterboot.py`):

| Set (clips) | Comparison | Metric | dF1 | Frame CI | Clip CI |
|---|---|---|---|---|---|
| valh (54) | with - without | BEV | +0.042 | [+0.037, +0.048] | [+0.028, +0.057] |
| valh (54) | with - without | image | +0.034 | [+0.028, +0.040] | [+0.019, +0.048] |
| valh (54) | with - Eq. (6) | BEV | +0.063 | [+0.055, +0.070] | [+0.045, +0.080] |
| val3 (54) | with - without | BEV | +0.041 | [+0.033, +0.050] | [+0.028, +0.054] |
| tr (406) | with - without | BEV | +0.056 | [+0.048, +0.063] | [+0.044, +0.071] |
| tr (406) | with - Eq. (6) | BEV | +0.058 | [+0.050, +0.066] | [+0.044, +0.073] |

Clip intervals are 1.7-2.5 times wider than frame intervals (frames of a clip
are correlated); protocol v2 therefore uses clip-level resampling for its
decisions.

## Reproduction

`scripts/devrun.py` (paths at the top: dev data copy and this folder's
calibration), configurations in `configs/`, lists in `lists/`. CULane images
are not redistributed.
