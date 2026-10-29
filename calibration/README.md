# CULane calibration (one homography per test folder)

Committed before the evaluation run (docs/EVAL_PROTOCOL.md, section 4).

## Procedure

1. Candidate frames: only non-evaluated test lists (crowd, shadow, arrow,
   cross). `scripts/scan_dash_period.py` fitted the two ego boundaries from the
   official annotation, measured brightness along them above the hood, and kept
   frames where one full dash period is visible. Hood rows used:
   driver_37 395, driver_100 440, driver_193 400.
2. The dash fraction (cross-ratio with the vanishing row) identifies the
   pattern: frames with 0.37-0.43 match 6 m dash + 9 m gap. Candidates were
   checked visually; frames where the run came from a vehicle, shadow,
   crosswalk or yellow centre line were rejected.
3. Rectangle: ego lane between the two boundary centrelines (fitted lines),
   3.75 m wide, from the far end of the near dash to the far end of the next
   dash (15 m). `scripts/make_homography.py` mapped it to the 225 x 300 BEV of an
   11.25 m x 15 m ROI (20 px/m) starting at the rectangle's near edge.

| Folder | Calibration frame (list) | Dashed side | Dash fraction |
|---|---|---|---|
| driver_37_30frame | 05181608_0235.MP4/03750.jpg (crowd) | right | 0.388 |
| driver_100_30frame | 05250538_0313.MP4/00300.jpg (crowd) | left | 0.408 |
| driver_193_90frame | 06050933_0603.MP4/02700.jpg (crowd) | left | 0.396 |

Rows and points are in `calibration_frames.json`; the homography files store
the points and sizes. `culane_<folder>.png` are BEV previews with a 1 m grid.

## Check on other non-evaluated frames (`calibration_qa.json`)

25 straight-road frames per folder, ego boundaries from the annotation warped
with the folder homography:

| Folder | Lane width median (IQR), assumed 3.75 m | abs. boundary angle median (90th pct) |
|---|---|---|
| driver_37_30frame | 4.11 m (3.81-4.36) | 1.25 deg (3.53) |
| driver_100_30frame | 4.44 m (4.14-4.65) | 0.85 deg (1.89) |
| driver_193_90frame | 3.47 m (3.27-3.66) | 1.05 deg (2.43) |

Straight boundaries stay well inside the +/-5 deg straight band. Lane-width
spread combines real lane-width differences between roads, frame-to-frame
pitch changes (vanishing row varies by about +/-10 px) and the 3.75 m
assumption; it is reported as calibration uncertainty.

## Limitations

- CULane frames show barrel distortion and no intrinsics are available; the
  homography is pinhole-only, used on the central road region above the hood.
- A fixed homography per folder ignores pitch changes between frames.
- The visible road band is short (about rows 270-440), so the far part of the
  15 m ROI is strongly upsampled.
