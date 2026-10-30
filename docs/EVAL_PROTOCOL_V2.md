# Pre-registered evaluation protocol v2 (corrected method)

Status: **registered before any CULane test frame is processed with the v2
method.** The registering commit, and the SHA-256 of `git archive` of that
commit sent to the co-authors before the run, fix this protocol. Later
changes are listed under *Deviations*.

## 0. Position of this evaluation

- v2 has not been run on the CULane test frames before registration.
- v2 is not blind to the test set. Two kinds of test-set information reached
  it: (1) the summary of the registered v1 test run (about half of the
  frames ended as `no_peaks` in both conditions), which started the
  development; (2) the v1 calibration of the test camera folders (clicked
  rectangles and hood rows, from non-evaluated test lists), which fixes the
  v2 test homographies and supplied the focal length used for one
  development calibration constant (`development/README.md`). No test frame
  was run or scored with any development candidate.
- All method choices were made on CULane train/val frames
  (`development/README.md`). The development confirmation set (`valh`) is
  interleaved with the tuning frames (same clips) and was used for several
  candidates; it is not an independent held-out set.
- v1 (`docs/EVAL_PROTOCOL.md`, results in
  `results/culane_paper_nominal_20261030/`) stays unchanged and is reported
  together with v2. Neither evaluation re-analyses the 297-frame set of the
  paper.

## 1. Method and conditions

Repository revision: the registering commit. Three conditions on the same
frames, homographies and evaluation:

| Condition | Configuration | Differs from v2 only in |
|---|---|---|
| `with_blsf` | `configs/v2.yaml` | - |
| `without_blsf` | `configs/v2_ablation_no_blsf.yaml` | `blsf.enabled: 0` |
| `with_blsf_eq6` | `configs/v2_eq6.yaml` | `blsf.decision: "sum"` (published Eq. 6) |

Unchanged from the paper: Sm = 9, Tg = 15, T1 = 17, BEV 225 x 300, bands
A0 = [-35, 0], A1 = [-5, 5], A2 = [0, 35] with length-weighted overlapping
votes (Eq. 5), the +/-35 deg envelope, and the form of the confidence gate
(low confidence when max_k B_k is below a threshold; no tracker input).
Unchanged from v1 (not published in the paper): the gate threshold 187.5 px
(the released code's 300 px at 640 x 480, scaled by 300 / 480) and the other
proportionally converted values in `configs/paper_nominal.yaml`.

Method modifications ([v2] in `configs/v2.yaml`); these change the published
method and are reported as such, not as parameter settings:

1. **Width-normalised band decision** (replaces Eq. 6): the retained band is
   argmax_k B_k / |A_k| (votes per degree) instead of argmax_k B_k. With raw
   sums the 35-degree curve bands, each containing half of the straight band,
   win on most frames with background texture and remove the boundary on the
   other side. Tie order unchanged (straight, left, right).
2. Initialisation: column histogram over the whole BEV (the lower half can
   fall inside a 9 m dash gap); no initial peak within 0.9 m of the BEV
   centre; each side is tracked on its own (status `partial` when only one
   side is found).
3. Tracker window margin 12 px (0.6 m).
4. Fit: least-squares refit on the RANSAC inliers; curvature bound
   |a| <= 5e-4 px^-1 (radius >= 50 m at 20 px/m); straight-line refit when
   the inliers span less than half of the BEV height; a side is output only
   if its inlier fraction is >= 0.5 (>= 0.7 when the other side has no
   output).
5. ROI start 0.5 m beyond the hood edge (section 2).

Fixed values with their development sensitivity (`development/README.md`):
the curvature bound is a nominal limit chosen from development sensitivity;
relative to the chosen R >= 50 m, overall F1 changed by at most 0.006 for
radii of 30-150 m. ROI start 0.25 / 0.5 / 1 / 2 m beyond the hood edge gave
decreasing F1; 0.5 m was chosen because the hood rows were read by eye in v1
and it leaves about 14 image rows between the ROI and the hood edge (about 7
at 0.25 m).

## 2. Data and calibration

- Same lists, annotations and frames as v1: `test2_hlight` (486 frames, 48
  clips), `test8_night` (7,029, 61), `test6_curve` (422, 70), `test0_normal`
  (9,621, 315). Every frame stays in the results.
- Homographies `calibration/v2/culane_<folder>.yml` from
  `scripts/make_v2_homographies.py`, using only the v1 calibration record
  (same rectangles, 3.75 m x 15 m; same hood rows 395 / 440 / 400). The ROI
  (11.25 m x 15 m, 20 px/m) starts at Y(hood row) + 0.5 m (`v2_roi.json`).

## 3. Evaluation

- Primary metric: the v1 BEV ego-lane metric with unchanged matching rules
  (`scripts/blsf_eval/evaluate.py`; 10 px, IoU >= 0.5, GT lane >= 100 BEV
  rows), applied in the v2 BEV. Because the v2 ROI starts nearer the camera,
  v1 and v2 scores cover different ground regions; comparisons between v1
  and v2 are descriptive, and the hypotheses below compare conditions within
  v2 only.
- Secondary metric: image-space ego-lane IoU, CULane-style
  (`scripts/blsf_eval/evaluate_image.py`; 30 px on 1640 x 590, IoU >= 0.5,
  same ego lanes, inside the BEV ROI region). Not the official CULane
  benchmark (all lanes, whole image).
- Point estimates: pooled precision, recall and F1 from summed TP, FP, FN.
- **Intervals and decisions: paired clip-level bootstrap**
  (`stats.cluster_bootstrap`). The resampling unit is the source video clip
  (`<driver folder>/<clip>.MP4`); 2,000 resamples, seed 20261029. In each
  resample the same clips are used for all three conditions, TP/FP/FN are
  re-summed and pooled P, R, F1 and the differences F1(with_blsf) -
  F1(other) recomputed; 95 % percentile intervals. For `all`, frames of one
  clip in different subsets form one cluster.
- Descriptive only (not used for decisions, because frames of a clip are
  correlated): frame-level bootstrap intervals, Wilson intervals for
  precision and recall, and exact McNemar tests on frames with both sides
  correct, as produced by the v1 code. No interval is computed for F1 by
  the Wilson method.

Hypotheses (pooled `all`, primary metric, clip-level intervals), tested in a
fixed sequence so that the probability of any false claim stays at 5 %:

1. H1: F1(with_blsf) > F1(without_blsf). Supported if the 95 % interval of
   the difference lies above 0.
2. H2: F1(with_blsf) > F1(with_blsf_eq6). Judged only if H1 is supported,
   with the same rule. If H1 is not supported, H2 is reported descriptively
   and not claimed.

Both differences and their intervals are reported in every case. Per-subset
results and the secondary metric are reported with their intervals and are
not tested (the dazzle and curve subsets have few clips). Development values
for orientation only (`valh`, BEV F1): 0.412 / 0.369 / 0.349; clip-level
intervals of the differences +0.028 to +0.057 (H1) and +0.045 to +0.080 (H2).

## 4. Execution

```bash
python3 scripts/run_experiment.py --spec experiments/culane_v2.local.json \
  --binary build/blsf_lane --work_dir work/culane_v2 --runs_only --max_frames_per_run 2500
python3 scripts/run_experiment.py --spec experiments/culane_v2.local.json \
  --work_dir work/culane_v2 --eval_only
```

Runs and scoring may be split and resumed (`--resume`); scoring uses Python
OpenCV 4.6.0 as in v1. Dry runs only on non-evaluated lists. Logs,
manifests, per-frame results and summaries are archived unchanged.

## 5. Figures and runtime

As in v1: figures chosen by rule (median-IoU true positive and first failure
per subset, `with_blsf`), program output only. ARM timing measured
separately with `--no_debug`.

## 6. Reporting

All results are reported whatever their direction: every subset, all three
conditions, both metrics, next to the v1 registered results. Known limits
from development: recall is limited by occluded and worn boundaries that
CULane annotates; absolute values are far below those in the paper.

## Deviations

None yet.
