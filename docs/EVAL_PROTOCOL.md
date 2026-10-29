# Pre-registered evaluation protocol for the corrected BLSF implementation

Status: **registered before any test frame is processed.** The commit that adds
this file fixes the protocol; its Git timestamp is the registration time. Any
later change is listed under *Deviations* with date and reason, and results are
reported for the registered settings as well.

This experiment is new. It does not reproduce the 297-frame self-collected
set or Tables 3, 6 and 7 of *Electronics* 2026, 15, 351, and it is not
presented as the program or data behind those tables.

## 1. Software

- Repository revision: the commit containing this file (or a later commit that
  changes only documentation or calibration files listed in section 4).
- Conditions (`blsf.enabled` is the only difference):
  - `configs/paper_nominal.yaml` (with BLSF)
  - `configs/paper_nominal_ablation_no_blsf.yaml` (without BLSF)
- Build: CMake Release. Compiler and OpenCV versions are recorded by
  `scripts/run_experiment.py` in `experiment_manifest.json`.

## 2. Data

Primary benchmark: **CULane test set**, official category lists from
`list/test_split/`:

| Subset | List file | Purpose |
|---|---|---|
| Dazzle light | `test2_hlight.txt` | strong backlight / glare |
| Night | `test8_night.txt` | low-contrast night |
| Curve | `test6_curve.txt` | curved roads |
| Normal | `test0_normal.txt` | reference condition |

Frame counts and SHA-256 hashes of the list files are recorded in the run
manifest. Annotations are the `.lines.txt` files distributed with the test
archives; any annotation update applied must be named in the manifest notes.

Not used, with reasons:

- **LLAMAS**: test annotations are not public and the dataset defines no
  official Night or Dazzle subsets.
- **CurveLanes**: about 76 GB in archives that mix splits; not feasible in the
  schedule. CULane Curve is used instead.
- **Rain**: CULane has no rain category. Rain-specific claims are either
  withdrawn or evaluated in a separately registered amendment on a dataset
  with camera calibration, registered before that data is processed.

## 3. Ground region and BEV grid

- BEV 225 x 300 px covering an 11.25 m x 15 m ground rectangle (3:4,
  `ipm.roi_w_over_l: 0.75`): 20 px/m on both axes, so pixel angles equal
  physical headings and the +/-35 and +/-5 degree bands are physical.
- Rationale (decided from geometry, before any test frame): a 15 cm marking is
  about 3 px, against the 9 px median window of MLT (Sm = 9), and the LSD
  minimum length T1 = 17 px (0.85 m) is below the shortest common dash (2 m).
  11.25 m covers the ego lane and both neighbouring lanes (3 x 3.75 m); 15 m is
  one 6 m + 9 m dash period.
- The ROI is centred laterally on the ego lane and starts at the near edge of
  the calibration rectangle.

## 4. Calibration

- One homography per CULane test folder (`driver_37_30frame`,
  `driver_100_30frame`, `driver_193_90frame`), assuming a fixed camera mount
  per vehicle.
- Calibration frames are taken from test categories **not evaluated here**
  (crowded, shadow, no-line, arrow, crossroad lists), chosen for a straight,
  flat road with both ego boundaries visible. No evaluated frame is used.
- The clicked rectangle is the ego lane between the two boundary-marking
  centrelines over one dash period. Assumed sizes: lane width 3.75 m; dash
  period 15 m (6 m dash + 9 m gap) where the dashes match that pattern,
  otherwise 6 m (2 m + 4 m). The values used are written into each `.yml`.
- `scripts/make_homography.py` writes the homography, the clicked points,
  rectangle and ROI sizes, and a preview with a 1 m grid. Acceptance check:
  in the preview the lane lines are vertical and parallel, and the dash length
  matches the assumed value on the grid. Previews are committed with the
  calibration files.
- Calibration files are committed before the evaluation run. A homography
  whose stored size differs from the configuration is rejected by the program.

## 5. Parameters

Paper values: Sm = 9, Tg = 15, T1 = 17, BEV 225 x 300. Pixel-unit values not
given in the paper are proportional conversions from the released 640 x 480
values (README, *Configurations*), with one exception decided on synthetic data
before any real frame:

- `peaks.min_peak_value = 12` instead of the proportional 31. The initial
  column histogram counts mask pixels in the lower half of the BEV after
  3-column smoothing; 12 is reached by one 2 m dash (40 rows) whose
  single-edge support is spread over the smoothing window (40 / 3 ~ 13).
  On synthetic frames (`evidence/validation/synthetic_sensitivity.md`,
  `scripts/synthetic_sensitivity.py`) the proportional value 31 gives F1 = 0
  for both conditions on short dashes and curves, which would measure the
  initialisation threshold rather than BLSF.

No parameter is changed after test frames are processed. Should a change be
unavoidable, the registered result is still reported and the change is
listed as a deviation.

## 6. Execution

```bash
python3 scripts/run_experiment.py --spec experiments/culane_paper_nominal.local.json \
  --binary build/blsf_lane --work_dir work/culane_paper_nominal
```

- Running and scoring may be split across machines (`--runs_only` on the
  machine with the images, `--eval_only` on the copied work directory plus
  annotations); this gives the same per-frame results and summary as a
  single run.
- Every listed frame stays in the results: rejected (`low_confidence`),
  `no_peaks`, `fit_failed` and unreadable frames count as frames without a
  prediction.
- Dry runs (`--limit`) are allowed only on non-evaluated lists (for example
  `test1_crowd.txt`) to check the setup; they are marked as dry runs.
- The work directory (mapping, per-run logs and manifests, `per_frame.csv`,
  `summary.json`, `experiment_manifest.json`) is archived unchanged. Images are
  not redistributed (CULane licence).

## 7. Evaluation

Ego-lane evaluation in the BEV ROI (`scripts/blsf_eval/evaluate.py`):

- GT lanes are warped into the BEV with the group homography; a lane counts if
  it covers at least 100 BEV rows (5 m).
- Ego boundaries: the counted lanes nearest the BEV centre on each side,
  measured at each lane's lowest covered row.
- Each side is scored separately. Prediction (x = a y^2 + b y + c) and GT are
  drawn 10 px wide (0.5 m); the prediction is restricted to the GT rows; a side
  is a true positive at IoU >= 0.5.
- Precision, recall, F1 per subset and pooled; Wilson 95% intervals for
  precision and recall; frame-level bootstrap (2000 resamples, seed 20261029)
  for F1 and for the paired F1 difference (with - without); exact McNemar test
  on frames where both sides are correct.
- Also reported: status counts and low-confidence rate per condition.
- This is not the official CULane metric (image space, up to four lanes) and
  is not comparable with CULane leaderboard numbers.

## 8. Figures

Only program output is used (`--debug_dir` images of `blsf_lane`). Frames are
chosen by rule, not by appearance: per subset, the frame with the median
with-BLSF IoU among true positives and the first failure in key order. Each
caption names the dataset, frame key, configuration and commit.

## 9. Runtime

ARM timing is measured separately on the 2 GHz ARM platform with
`--no_debug`, reporting `pipeline_ms` (image read and file writes excluded),
hardware, compiler flags and frame count. It replaces Table 4 only when that
measurement exists.

## 10. Reporting

All registered results are reported whatever their direction, including
subsets where BLSF does not help. Known weakness measured before the run: on
synthetic curves (curvature coefficient 0.012) F1 is about 0.56 for both
conditions.

## Deviations

None yet.
