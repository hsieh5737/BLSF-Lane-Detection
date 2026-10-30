# Registered CULane evaluation, paper nominal setting (run 2026-10-30)

Protocol: docs/EVAL_PROTOCOL.md (registered in 3eeaabc). Software: commit
7202925; calibration: calibration/ (dde596e). Program runs used
`--runs_only --max_frames_per_run 2500`; scoring used `--eval_only` in an
identical conda environment (OpenCV 4.6.0, numpy 1.26.4, Python 3.10.13),
verified to reproduce the scoring of a dry run byte for byte.

Files: summary.md / summary.json (all registered statistics), per_frame.csv
(every frame and condition, including rejections and failures),
run_manifest.json (input, config, homography and binary hashes),
eval_manifest.json, mapping.csv (frame key to staged file). The raw run
directory (per-run predictions, logs, manifests) is archived as runs.tgz with
the SHA-256 in runs_archive.sha256. CULane images are not redistributed.

Metric: ego-lane BEV IoU (section 7 of the protocol); not the official CULane
metric and not comparable with CULane leaderboards or the article's tables.
