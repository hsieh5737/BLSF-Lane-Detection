# BLSF corrected candidate

> **Correction notice (2026-10-29).** A PubPeer comment on
> *Electronics* 2026, 15, 351 (https://doi.org/10.3390/electronics15020351)
> showed that the originally released code did not consistently implement the
> method described in the article (angle convention, orientation gating,
> low-evidence rejection and tracker input). The main branch now contains a
> corrected implementation. It is not the program that produced the originally
> reported results; reconciliation of those results is in progress, and this
> implementation may still change during validation. The original release is
> preserved unchanged at commit
> [830a62f](https://github.com/hsieh5737/BLSF-Lane-Detection/tree/830a62f5eaf4bd1d74bc3be11451881cc3c9a0cf).

This package repairs the released C++ snapshot
`830a62f5eaf4bd1d74bc3be11451881cc3c9a0cf`.
Read [RECONSTRUCTION_STATUS.txt](RECONSTRUCTION_STATUS.txt) before using it.

It is a new corrected candidate, not a recovered experiment and not validation of
the published Tables 6 and 7. Original data, annotations, evaluator and ARM logs
remain necessary.

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
