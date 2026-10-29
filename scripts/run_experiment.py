#!/usr/bin/env python3
"""Run a pre-registered BLSF experiment from a JSON spec (docs/EVAL_PROTOCOL.md).

Stages frames into flat folders per (subset, calibration group), runs every
condition through scripts/run_audit.py with the group's homography, evaluates
each frame, and writes per-frame results, summaries and a provenance manifest.
Every listed frame stays in the results, including rejected and failed ones.
"""
import argparse, csv, datetime, hashlib, json, os, platform, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import cv2  # noqa: E402
import numpy as np  # noqa: E402
from blsf_eval import datasets, evaluate as ev, geometry as geo  # noqa: E402


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def resolve(p, base):
    p = Path(p)
    return p if p.is_absolute() else (base / p)


def config_bev(path):
    fs = cv2.FileStorage(str(path), cv2.FILE_STORAGE_READ)
    if not fs.isOpened():
        raise SystemExit(f"cannot read config {path}")
    w = int(fs.getNode("ipm").getNode("bev_width").real())
    h = int(fs.getNode("ipm").getNode("bev_height").real())
    fs.release()
    return w, h


def git_revision():
    try:
        rev = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"], capture_output=True, text=True)
        dirty = subprocess.run(["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=no"],
                               capture_output=True, text=True)
        return {"commit": rev.stdout.strip() or None, "dirty": bool(dirty.stdout.strip())}
    except OSError:
        return {"commit": None, "dirty": None}


def safe_name(key):
    return re.sub(r"[^A-Za-z0-9._-]", "_", key.replace("/", "__"))


def link_or_copy(src, dst):
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True)
    ap.add_argument("--binary", help="required unless --eval_only")
    ap.add_argument("--work_dir", required=True)
    ap.add_argument("--resume", action="store_true", help="reuse completed runs in work_dir")
    ap.add_argument("--limit", type=int, default=0, help="DRY RUN: first N frames per subset")
    ap.add_argument("--runs_only", action="store_true", help="stage and run, then stop (score elsewhere)")
    ap.add_argument("--eval_only", action="store_true",
                    help="score the runs already in work_dir (mapping.csv, runs/); no staging or runs")
    a = ap.parse_args()
    if a.runs_only and a.eval_only:
        raise SystemExit("--runs_only and --eval_only are exclusive")
    if not a.eval_only and not a.binary:
        raise SystemExit("--binary is required unless --eval_only")

    spec_path = Path(a.spec).resolve()
    spec = json.loads(spec_path.read_text())
    work = Path(a.work_dir).resolve()
    if os.name == "nt":  # MinGW OpenCV cannot open non-ASCII paths
        paths = [work, REPO, Path(spec["root"])] + ([Path(a.binary).resolve()] if a.binary else [])
        bad = [str(x) for x in paths if not str(x).isascii()]
        if bad:
            raise SystemExit(f"use ASCII-only paths on Windows; offending: {bad}")
    if work.exists() and any(work.iterdir()) and not (a.resume or a.eval_only):
        raise SystemExit("work_dir must be empty (or use --resume)")
    work.mkdir(parents=True, exist_ok=True)
    root = Path(spec["root"])
    params = ev.EvalParams(**spec.get("eval", {}))
    conds = spec["conditions"]
    if set(conds) != {"with_blsf", "without_blsf"}:
        raise SystemExit("conditions must be exactly with_blsf and without_blsf")
    cfg = {k: resolve(v, REPO) for k, v in conds.items()}
    sizes = {k: config_bev(v) for k, v in cfg.items()}
    if len(set(sizes.values())) != 1:
        raise SystemExit(f"conditions use different BEV sizes: {sizes}")
    bev_w, bev_h = next(iter(sizes.values()))
    homs = {g: resolve(p, REPO) for g, p in spec["homographies"].items()}
    Hs = {}
    for g, p in homs.items():
        H, w, h = geo.load_homography_yml(p)
        if (w, h) != (bev_w, bev_h):
            raise SystemExit(f"homography {p} is {w}x{h}, configs need {bev_w}x{bev_h}")
        Hs[g] = H

    adapter = datasets.ADAPTERS[spec["dataset"]]
    subsets = {}
    for name, lst in spec["subsets"].items():
        items = adapter(root, resolve(lst, root), spec.get("exclude", []))
        if a.limit:
            items = items[:a.limit]
        missing_h = sorted({i.group for i in items} - set(Hs))
        if missing_h:
            raise SystemExit(f"subset {name}: no homography for groups {missing_h}")
        missing = [] if a.eval_only else [str(i.image) for i in items if not i.image.exists()]
        if missing:
            raise SystemExit(f"subset {name}: {len(missing)} images missing, e.g. {missing[:5]}")
        subsets[name] = items

    manifest = {"schema": "blsf-experiment-v1", "spec": spec, "spec_sha256": sha(spec_path),
                "dry_run": bool(a.limit), "limit": a.limit, "repository": git_revision(),
                "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "platform": platform.platform(), "python": sys.version, "opencv_python": cv2.__version__,
                "binary_sha256": sha(a.binary) if a.binary else None, "mode": ("eval_only" if a.eval_only else "runs_only" if a.runs_only else "full"),
                "configs": {k: {"path": str(v), "sha256": sha(v)} for k, v in cfg.items()},
                "homographies": {g: {"path": str(p), "sha256": sha(p)} for g, p in homs.items()},
                "lists": {n: {"path": str(resolve(l, root)), "sha256": sha(resolve(l, root)),
                              "frames": len(subsets[n])} for n, l in spec["subsets"].items()},
                "eval_params": ev.params_dict(params), "bev": [bev_w, bev_h]}
    if manifest["repository"]["dirty"]:
        print("WARNING: repository has uncommitted changes; record them before reporting", file=sys.stderr)

    mapping = {}
    if a.eval_only:
        with open(work / "mapping.csv", newline="") as fh:
            for row in csv.DictReader(fh):
                mapping[(row["subset"], row["staged_name"])] = row["key"]
        listed = {(n, it.key) for n, items in subsets.items() for it in items}
        if {(s_, k) for (s_, _), k in mapping.items()} != listed:
            raise SystemExit("mapping.csv does not match the spec's frame lists")
    # 1) stage
    stage = work / "stage"
    with (open(os.devnull, "w") if a.eval_only else open(work / "mapping.csv", "w", newline="")) as fh:
        w = csv.writer(fh)
        w.writerow(["subset", "group", "key", "staged_name"])
        for name, items in ({} if a.eval_only else subsets).items():
            for it in items:
                d = stage / name / it.group
                d.mkdir(parents=True, exist_ok=True)
                dst = d / (safe_name(it.key) + it.image.suffix.lower())
                if not dst.exists():
                    link_or_copy(it.image, dst)
                mapping[(name, dst.name)] = it.key
                w.writerow([name, it.group, it.key, dst.name])

    # 2) run each condition per subset/group
    for cond, cpath in ({} if a.eval_only else cfg).items():
        for name, items in subsets.items():
            for g in sorted({i.group for i in items}):
                out = work / "runs" / cond / name / g
                done = out / "manifest.json"
                if a.resume and done.exists() and json.loads(done.read_text()).get("exit_code") == 0:
                    continue
                if out.exists():
                    shutil.rmtree(out)
                cmd = [sys.executable, str(HERE / "run_audit.py"), "--binary", a.binary, "--config", str(cpath),
                       "--input_dir", str(stage / name / g), "--homography", str(homs[g]),
                       "--output_dir", str(out), "--no_debug"]
                print("RUN", cond, name, g, flush=True)
                r = subprocess.run(cmd)
                if r.returncode:
                    raise SystemExit(f"run failed: {cond}/{name}/{g}")

    if a.runs_only:
        manifest["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        ev.dump_json(work / "run_manifest.json", manifest)
        print("runs complete; score with --eval_only", flush=True)
        return

    # 3) evaluate
    res = work / "results"
    res.mkdir(exist_ok=True)
    per_frame, by = [], {}
    for name, items in subsets.items():
        gts = {it.key: ev.gt_ego_lanes(it.lanes, Hs[it.group], bev_w, bev_h, params) for it in items}
        for cond in cfg:
            preds = {}
            for g in sorted({i.group for i in items}):
                for row in ev.read_predictions(work / "runs" / cond / name / g / "predictions.csv"):
                    staged = re.split(r"[\\/]", row["image"])[-1]
                    preds[mapping[(name, staged)]] = row
            frames = []
            for it in items:
                row = preds.get(it.key)
                if row is None:
                    raise SystemExit(f"no prediction row for {it.key} ({cond})")
                f = ev.score_frame(row, gts[it.key], bev_w, bev_h, params)
                f.update(condition=cond, subset=name, group=it.group, key=it.key, status=row["status"])
                frames.append(f)
            by[(cond, name)] = frames
            per_frame += frames
    ev.write_per_frame(res / "per_frame.csv", per_frame)

    summary = {"dry_run": bool(a.limit), "eval_params": ev.params_dict(params), "subsets": {}}
    names = list(subsets) + (["all"] if len(subsets) > 1 else [])
    for name in names:
        get = (lambda c: [f for n in subsets for f in by[(c, n)]]) if name == "all" else (lambda c: by[(c, name)])
        wb, wo = get("with_blsf"), get("without_blsf")
        summary["subsets"][name] = {"with_blsf": ev.summarize(wb, params, paired=wo),
                                    "without_blsf": ev.summarize(wo, params)}
    ev.dump_json(res / "summary.json", summary)

    lines = ["| Subset | Condition | Frames | P | R | F1 [95% CI] | Low-conf. |", "|---|---|---|---|---|---|---|"]
    for name, d in summary["subsets"].items():
        for cond in ("with_blsf", "without_blsf"):
            s = d[cond]
            lines.append(f"| {name} | {cond} | {s['frames']} | {s['precision']:.3f} | {s['recall']:.3f} | "
                         f"{s['f1']:.3f} [{s['f1_ci'][0]:.3f}, {s['f1_ci'][1]:.3f}] | {s['low_confidence_rate']:.3f} |")
        s = d["with_blsf"]
        lines.append(f"| {name} | delta F1 (with - without) | | | | [{s['delta_f1_ci'][0]:+.3f}, "
                     f"{s['delta_f1_ci'][1]:+.3f}] | McNemar p={s['mcnemar']['p_exact']:.3g} |")
    if a.limit:
        lines.insert(0, "**DRY RUN on a truncated list - not a result.**\n")
    (res / "summary.md").write_text("\n".join(lines) + "\n")

    manifest["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest["result_files"] = {p.name: sha(p) for p in sorted(res.iterdir()) if p.is_file()}
    ev.dump_json(work / ("eval_manifest.json" if a.eval_only else "experiment_manifest.json"), manifest)
    print((res / "summary.md").read_text())


if __name__ == "__main__":
    main()
