# BLSF corrected candidate

> **Correction notice.** A PubPeer comment on *Electronics* 2026, 15, 351
> (https://doi.org/10.3390/electronics15020351) showed that the originally
> released code did not consistently implement the method described in the
> article (angle convention, orientation gating, low-evidence rejection and
> tracker input). The original release is preserved unchanged at commit
> [830a62f](https://github.com/hsieh5737/BLSF-Lane-Detection/tree/830a62f5eaf4bd1d74bc3be11451881cc3c9a0cf).
> The authors do not rely on the originally reported results (297-frame set,
> Tables 3, 6 and 7) and have replaced them with two new evaluations on the
> public CULane test set (17,558 frames), reported in full. The protocols were
> fixed before their respective test runs and are archived in this repository:
>
> - **v1** (`docs/EVAL_PROTOCOL.md`, `results/culane_paper_nominal_20261030/`):
>   the corrected code at the paper's nominal setting. Pooled ego-lane F1
>   0.290 with and 0.292 without BLSF; the article's claims are not supported
>   at this setting.
> - **v2** (`docs/EVAL_PROTOCOL_V2.md`, `results/culane_v2_20261030/`): a
>   corrected method developed afterwards on CULane train/val data only
>   (`development/README.md`), including a width-normalised band decision
>   that replaces Eq. (6). Pooled F1 0.559 with BLSF, 0.538 without BLSF and
>   0.527 with the published Eq. (6); both differences are positive with
>   clip-level 95 % intervals above zero. BLSF helps most at night and is
>   worse than no BLSF on the curve subset.
>
> The form of the correction of the article is being settled with the
> journal.

The code below is the corrected implementation. It is not the program that
produced the originally reported results; see
[RECONSTRUCTION_STATUS.txt](RECONSTRUCTION_STATUS.txt). Original data,
annotations, evaluator and ARM logs of the article remain unavailable.

## Build and verify

Requires a C++17 compiler, CMake >=3.16 and OpenCV with core, imgproc, imgcodecs,
highgui. Tested locally with GCC 13.3.0 and OpenCV C++ 4.6.0. The commenter used
4.13.0; this package does not claim exact version-matched replication.

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j2
ctest --test-dir build --output-on-failure
./build/regression .
./build/legacy_probe
python3 -m unittest discover -s tests -p 'test_*.py'
```

Python helpers need numpy and opencv-python; Python's OpenCV version may differ
from the C++ library and is recorded separately in local validation notes.

## Audit a new run

Use an actual calibrated homography. Do not use the identity synthetic homography
for road images. Supply an empty output directory outside the input directory.
The image loader reads only the immediate input directory, not nested folders.
Image stems must be unique. RANSAC retains the upstream seed 12345.

```bash
python3 scripts/run_audit.py --binary build/blsf_lane \
  --config configs/default.yaml --input_dir data/frames \
  --homography calibration/homography.yml --output_dir outputs/with_blsf
python3 scripts/run_audit.py --binary build/blsf_lane \
  --config configs/ablation_no_blsf.yaml --input_dir data/frames \
  --homography calibration/homography.yml --output_dir outputs/without_blsf
```

For the paper's nominal setting use `configs/paper_nominal.yaml` and
`configs/paper_nominal_ablation_no_blsf.yaml` with a 225x300 homography of a
3:4 ground rectangle.

The paired configurations differ only in `blsf.enabled`. Both use the same LSD,
length threshold, segment rasterizer, tracker and RANSAC. The off condition
disables angular voting/gating and the low-evidence rejection together.
This estimates the full BLSF-stage contribution, not the angle gate alone.
A separate rejection-only ablation is needed to isolate that mechanism.

Each output includes BEV polynomial predictions, failures, debug masks, the
exact configuration and homography, source/input/executable SHA-256 hashes,
raw logs and manifest. A failed frame stays in predictions.csv.
`pipeline_ms` includes debug image construction inside run_pipeline but excludes
image reading and debug-file writing. It is not comparable to the paper's ARM
timing without matching hardware and timing scope.

## Configurations

Every configuration declares a 3:4 ground ROI (`ipm.roi_w_over_l: 0.75`).
The homography must map a ground rectangle with that width:length ratio to the
configured BEV size; a homography stored with a different BEV size is rejected.
The run prints sx/sy and the physical headings that the pixel-angle bands
represent, using tan(theta_pixel) = (sx/sy) tan(theta_physical).

| File | BEV | Use |
|---|---|---|
| `v2.yaml` / `v2_ablation_no_blsf.yaml` / `v2_eq6.yaml` | 225x300, isotropic | corrected method v2 and its registered controls (`docs/EVAL_PROTOCOL_V2.md`) |
| `paper_nominal.yaml` / `paper_nominal_ablation_no_blsf.yaml` | 225x300, isotropic | paired evaluation at the paper's nominal setting (v1) |
| `default.yaml` / `ablation_no_blsf.yaml` | 640x480, sx/sy=1.78 | released resolution under corrected logic |
| `legacy_params_640x480.yaml` | 640x480, sx/sy=1.78 | released numeric values under corrected logic, for tracing differences |

Paper values: Sm=9, Tg=15, T1=17. Other pixel-unit values in
`paper_nominal.yaml` are proportional conversions from 640x480, fixed before
any evaluation: kx = 225/640 for lateral sizes, ky = 300/480 for forward sizes,
and pixel counts scaled by line thickness ratio x ky. The one exception,
`peaks.min_peak_value`, was set from synthetic frames before any real frame
(`docs/EVAL_PROTOCOL.md`, `evidence/validation/synthetic_sensitivity.md`).

| Key | 640x480 | 225x300 | Rule |
|---|---|---|---|
| blsf.min_total_vote | 300 | 187.5 | x ky |
| blsf.draw_thickness | 2 | 1 | x kx, min 1 |
| peaks.smooth_ksize | 9 | 3 | x kx, odd |
| peaks.min_peak_value | 50 | 12 | not proportional (31 would be); see protocol section 5 |
| tracker.n_windows | 12 | 12 | count |
| tracker.margin | 60 | 21 | x kx |
| tracker.minpix | 40 | 13 | x (1/2) x ky |
| ransac.inlier_thresh | 10 | 3.5 | x kx |
| ransac.min_inliers | 80 | 25 | x (1/2) x ky |

## Evaluation protocols

v2 (`docs/EVAL_PROTOCOL_V2.md`): homographies `calibration/v2/` from
`scripts/make_v2_homographies.py`, specification `experiments/culane_v2.json`
(three conditions, secondary image-space metric, clip-level bootstrap), run as
below with `--runs_only` / `--eval_only`. Development record and every
development score: `development/`.

v1: `docs/EVAL_PROTOCOL.md` fixes data, calibration, parameters and metrics before
any run. Workflow:

1. Calibrate one homography per CULane test folder from a frame of a
   non-evaluated list:
   `python3 scripts/make_homography.py --image <frame> --pick --rect_w_m 3.75 --rect_l_m 15 --out calibration/culane_<folder>.yml --preview calibration/culane_<folder>.png`
2. Commit the calibration files and previews.
3. Copy `experiments/culane_paper_nominal.json` to `*.local.json`, set `root`.
4. `python3 scripts/run_experiment.py --spec experiments/culane_paper_nominal.local.json --binary build/blsf_lane --work_dir work/culane_paper_nominal`
5. Archive the whole work directory; report `results/summary.md` and
   `results/summary.json` unchanged.

On Windows (MSYS2 UCRT64) all paths must be ASCII-only; see `docs/RUN_WINDOWS.md`.
`tests/test_eval_pipeline.py` runs the same chain on rendered synthetic frames.

## Angle contract

Image x points right; y points down. The undirected segment angle is
`wrap_[-90,90)(atan2(dx,-dy)*180/pi)`. Upward vertical and downward vertical both
map to 0. Positive values lean right as y decreases. Endpoint reversal is invariant.

Closed bins preserve overlapping membership from Eq. (5); a segment may add its
length to more than one score. The overlap therefore never enters a rejection
denominator. A frame is low-confidence when every bin score is below the
absolute threshold, `max(B0,B1,B2) < min_total_vote`, as stated in the paper.
Because the selected band equals the winning bin, `max(B0,B1,B2)` is exactly
the total segment length passed to the tracker (`retained_vote` in the CSV).
There is no dominance-ratio gate: A0 and A2 together cover [-35,35], so
`dom_ratio = max(B0,B1,B2) / sum_unique(length)` is always >= 0.5 and any
threshold at or below 0.5 could never fire. It is reported for diagnosis only,
and a legacy `min_dom_ratio` key makes the configuration invalid.
Ties prefer straight, then left, then right. These are disclosed repair choices,
not recovered historical settings.

The overall envelope is fixed at |theta| <= 35 degrees in BEV pixel
coordinates; any other `max_abs_angle` is rejected. The winning bin then sets
the acceptance band exactly: left [-35,0], straight [-5,5], right [0,35].
No delta expansion or near-zero exclusion is permitted in this candidate.
LSD and BLSF use strict `length > T1`.

## Feature contract

Default tracker input is the 0/255 rasterized retained-segment mask S.
Rejected original pixels outside S remain zero in the tracker input.
Rasterization can add pixels, so S is not guaranteed to be a subset of B.
Optional `binary_and_segments` returns B intersection S; it changes feature
semantics and must be evaluated separately. Optional `binary` is a diagnostic
control and cannot support a claim of binary-pixel removal by BLSF.
Legacy hybrid keys are rejected rather than silently translated.

## Diagnostic mask evaluation

```bash
python3 scripts/evaluate_masks.py --predictions masks/pred \
  --ground_truth masks/gt --output diagnostic_scores.json
```

Requires identical nonempty PNG filename sets, equal shapes, already aligned
masks and values 0/255. It reports pooled pixel counts and micro metrics.
It is NOT an official CULane/LLAMAS lane-instance evaluator and cannot fill
published Table 7. The segment mask is an intermediate feature, not a lane
prediction mask. Before evaluation, generate prediction masks from the fitted
polynomials using a declared line width and coordinate transform.

## Evidence

- `evidence/upstream/`: unchanged original files, including original README.
- `evidence/upstream_manifest.json`: exact upstream blob hashes.
- `evidence/validation/`: observed local regression and smoke-run outputs.

Preserve the original repository revision and publish a new correction commit
after author review. Do not replace the original history or call this package
the historical code that produced the reported results.
