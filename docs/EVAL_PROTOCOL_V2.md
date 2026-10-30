# Pre-registered evaluation protocol v2 (corrected method)

Status: **registered before any CULane test frame is processed with the v2
method.** The registering commit, and the SHA-256 of `git archive` of that
commit sent to the co-authors before the run, fix this protocol. Later changes
are listed under *Deviations*.

## 1. Relation to the v1 protocol

`docs/EVAL_PROTOCOL.md` (v1) and its results
(`results/culane_paper_nominal_20261030/`) stay unchanged and are reported
together with the v2 results. v1 showed that the published configuration does
not reproduce the paper's claims; v2 evaluates a corrected method developed
afterwards on CULane train/val data only (`development/README.md`). v2 is a
new evaluation, not a re-analysis of the 297-frame set of the paper.

## 2. Software and conditions

Repository revision: the registering commit. Three conditions on the same
frames, homographies and evaluation:

| Condition | Configuration | Differs from v2 only in |
|---|---|---|
| `with_blsf` | `configs/v2.yaml` | - |
| `without_blsf` | `configs/v2_ablation_no_blsf.yaml` | `blsf.enabled: 0` |
| `with_blsf_eq6` | `configs/v2_eq6.yaml` | `blsf.decision: "sum"` (published Eq. 6) |

Unchanged from the paper: Sm = 9, Tg = 15, T1 = 17, BEV 225 x 300, bands
A0 = [-35, 0], A1 = [-5, 5], A2 = [0, 35] with length-weighted overlapping
votes (Eq. 5), the +/-35 deg envelope and the confidence gate
(max_k B_k < 187.5 => low confidence, no tracker input).

Changes ([v2] in `configs/v2.yaml`):

1. Winning band by votes per degree, argmax_k B_k / |A_k|, instead of
   argmax_k B_k. The 35-degree curve bands each contain half of the straight
   band, so with raw sums they win on most frames with background texture and
   discard the boundary on the other side.
2. Initialisation: column histogram over the whole BEV (not the lower half,
   which can fall inside a 9 m dash gap); no initial peak within 0.9 m of the
   BEV centre; each side is tracked on its own (a frame with one boundary
   yields one side, status `partial`).
3. Tracker window margin 12 px (0.6 m).
4. Fit: least-squares refit on the RANSAC inliers, curvature bound
   |a| <= 3e-4 px^-1 (radius >= about 83 m), straight-line refit when the
   inliers span less than half of the BEV height; a side is output only if
   its inlier fraction is >= 0.5 (>= 0.7 when the other side has no output).
5. ROI start 0.5 m beyond the hood edge (section 3).

## 3. Data and calibration

- Same lists, annotations and frames as v1: `test2_hlight` (486),
  `test8_night` (7,029), `test6_curve` (422), `test0_normal` (9,621). Every
  frame stays in the results.
- Homographies `calibration/v2/culane_<folder>.yml`, made by
  `scripts/make_v2_homographies.py` from the v1 calibration record only (same
  clicked rectangles, 3.75 m x 15 m; same hood rows 395 / 440 / 400). The ROI
  (11.25 m x 15 m, 20 px/m) starts at Y(hood row) + 0.5 m; `v2_roi.json`
  lists the offsets (-1.462, -3.762, -0.137 m from the rectangle's near edge).
  No test frame was used.

## 4. Evaluation

- Primary metric: the v1 BEV ego-lane metric, unchanged
  (`scripts/blsf_eval/evaluate.py`; 10 px, IoU >= 0.5, GT lane >= 100 BEV
  rows), evaluated in each condition's BEV, i.e. with the v2 homographies.
- Secondary metric: image-space ego-lane IoU, CULane-style
  (`scripts/blsf_eval/evaluate_image.py`; lanes drawn 30 px wide on
  1640 x 590, IoU >= 0.5, the same ego lanes, inside the BEV ROI region).
  This is not the official CULane benchmark (all lanes, whole image).
- Per subset and pooled (`all`): precision, recall, F1 with Wilson and frame
  bootstrap 95 % intervals (2,000 resamples, seed 20261029); paired F1
  differences with bootstrap intervals and exact McNemar tests on frames with
  both sides correct, for `with_blsf - without_blsf` and
  `with_blsf - with_blsf_eq6`; status counts and low-confidence rate.

Hypotheses (pooled `all`, primary metric):
H1 F1(with_blsf) > F1(without_blsf); H2 F1(with_blsf) > F1(with_blsf_eq6).
Supported if the 95 % bootstrap interval of the difference lies above 0.
Development values for orientation only (held-out validation frames):
0.417 / 0.375 / 0.352.

## 5. Execution

```bash
python3 scripts/run_experiment.py --spec experiments/culane_v2.local.json \
  --binary build/blsf_lane --work_dir work/culane_v2 --runs_only --max_frames_per_run 2500
python3 scripts/run_experiment.py --spec experiments/culane_v2.local.json \
  --work_dir work/culane_v2 --eval_only
```

Runs and scoring may be split and resumed (`--resume`); scoring uses
Python OpenCV 4.6.0 as in v1. Dry runs only on non-evaluated lists.
Logs, manifests, per-frame results and summaries are archived unchanged.

## 6. Figures and runtime

As in v1: figures chosen by rule (median-IoU true positive and first failure
per subset, `with_blsf`), program output only. ARM timing measured
separately with `--no_debug`.

## 7. Reporting

All results are reported whatever their direction: every subset, all three
conditions, both metrics, next to the v1 registered results. Known limits
from development: recall is limited by occluded and worn boundaries that
CULane annotates; absolute values are far below those in the paper.

## Deviations

None yet.
