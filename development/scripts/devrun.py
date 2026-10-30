#!/usr/bin/env python3
"""Development runner on CULane train/val frames only (never test lists)."""
import argparse, csv, json, os, pickle, re, subprocess, sys, time
from pathlib import Path
import numpy as np
R = Path.home() / "BLSF-Lane-Detection"
sys.path.insert(0, str(R / "scripts"))
from blsf_eval import datasets, evaluate as ev, evaluate_image as ei, geometry as geo, stats

DEV = Path.home() / "dev"
ROOT = Path.home() / "devdata"
BATCH = 300
T0 = time.time()


def subsets():
    val = [l.strip() for l in open(ROOT / "dev_val.txt") if l.strip()]
    tr = [l.strip() for l in open(ROOT / "dev_train_sample.txt") if l.strip()]
    return {"val3": val[::3], "val": val, "valh": [k for i, k in enumerate(val) if i % 3],
            "tr": [k for k in tr if not k.startswith("/driver_23_")]}


def items(name):
    pk = DEV / f"items_{name}.pkl"
    if pk.exists():
        return pickle.loads(pk.read_bytes())
    keys = subsets()[name]
    lst = DEV / f"list_{name}.txt"; lst.write_text("\n".join(keys) + "\n")
    it = datasets.culane_items(ROOT, lst)
    pk.write_bytes(pickle.dumps(it))
    return it


def stage(name):
    it = items(name)
    by = {}
    for i in it:
        by.setdefault(i.group, []).append(i)
    mp = {}
    for g, lst in by.items():
        for j, i in enumerate(lst):
            d = DEV / "stage" / name / g / f"b{j // BATCH:03d}"
            d.mkdir(parents=True, exist_ok=True)
            fn = re.sub(r"[^A-Za-z0-9._-]", "_", i.key.replace("/", "__"))
            if not (d / fn).exists():
                os.symlink(i.image, d / fn)
            mp[fn] = i.key
    return it, mp


def run(cfg, calib, name, budget, jobs=2):
    stage(name)
    tag = Path(cfg).stem + "__" + calib
    todo = []
    for b in sorted((DEV / "stage" / name).glob("*/b*")):
        g = b.parent.name
        out = DEV / "runs" / tag / name / g / b.name
        if (out / "manifest.json").exists() and (out / "predictions.csv").exists() and json.loads((out / "manifest.json").read_text()).get("exit_code") == 0:
            continue
        todo.append((b, g, out))
    running = []
    while todo or running:
        while todo and len(running) < jobs and time.time() - T0 < budget:
            b, g, out = todo.pop(0)
            if out.exists():
                import shutil; shutil.rmtree(out)
            p = subprocess.Popen([sys.executable, str(R / "scripts/run_audit.py"), "--binary", str(R / "build/blsf_lane"),
                                  "--config", str(cfg), "--input_dir", str(b), "--homography",
                                  str(DEV / "calib" / f"{g}_{calib}.yml"), "--output_dir", str(out), "--no_debug"],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            running.append((p, out))
        if not running:
            print("budget reached; run again"); return False
        time.sleep(0.2)
        for p, out in list(running):
            if p.poll() is not None:
                running.remove((p, out))
                if p.returncode:
                    sys.exit(f"failed {out}: {p.stderr.read().decode()[-500:]}")
    return True


def score(cfg, calib, name, pe=ev.EvalParams(), pi=ei.ImageEvalParams()):
    it, mp = stage(name)
    tag = Path(cfg).stem + "__" + calib
    cache = DEV / "scores" / f"{tag}__{name}.pkl"
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    preds = {}
    for f in (DEV / "runs" / tag / name).glob("*/b*/predictions.csv"):
        for row in csv.DictReader(open(f)):
            preds[mp[re.split(r"[\\/]", row["image"])[-1]]] = row
    Hs, rois = {}, {}
    frames = []
    for i in it:
        if i.group not in Hs:
            H, w, h = geo.load_homography_yml(DEV / "calib" / f"{i.group}_{calib}.yml")
            Hs[i.group] = (H, w, h); rois[i.group] = ei.roi_mask(ei.bev_to_image(H, w, h), w, h, pi)
        H, w, h = Hs[i.group]
        row = preds[i.key]
        fb = ev.score_frame(row, ev.gt_ego_lanes(i.lanes, H, w, h, pe), w, h, pe)
        fi = ei.score_frame_image(row, i.lanes, H, w, h, pe, pi, rois[i.group])
        frames.append(dict(key=i.key, group=i.group, status=row["status"], b=(fb["tp"], fb["fp"], fb["fn"]),
                           i=(fi["tp"], fi["fp"], fi["fn"]), bok=fb["frame_ok"], iok=fi["frame_ok"],
                           iou=(fb["iou_left"], fb["iou_right"]), gt=(fb["gt_left"], fb["gt_right"])))
    cache.parent.mkdir(exist_ok=True); cache.write_bytes(pickle.dumps(frames))
    return frames


def summ(frames):
    out = {}
    for m in ("b", "i"):
        tp, fp, fn = np.array([f[m] for f in frames]).sum(0)
        P, Rr, F = stats.prf(tp, fp, fn); out[m] = (P, Rr, F)
    st = {}
    for f in frames:
        st[f["status"]] = st.get(f["status"], 0) + 1
    out["status"] = st
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd"); ap.add_argument("--cfg", nargs="+"); ap.add_argument("--calib", default="h2")
    ap.add_argument("--sub", nargs="+", default=["val3", "tr"]); ap.add_argument("--budget", type=float, default=150)
    a = ap.parse_args()
    if a.cmd == "run":
        ok = True
        for c in a.cfg:
            for s in a.sub:
                ok &= run(c, a.calib, s, a.budget)
                if not ok: break
            if not ok: break
        print("ALL DONE" if ok else "PARTIAL")
    elif a.cmd == "score":
        import multiprocessing as mpc
        jobs = [(c, a.calib, s) for c in a.cfg for s in a.sub]
        with mpc.Pool(2) as pool:
            res = pool.starmap(score, jobs)
        for (c, _, s), fr in zip(jobs, res):
                S = summ(fr)
                print(f"{Path(c).stem:28s} {a.calib:4s} {s:5s} n={len(fr):5d} BEV P/R/F1 {S['b'][0]:.3f}/{S['b'][1]:.3f}/{S['b'][2]:.3f}"
                      f"  IMG P/R/F1 {S['i'][0]:.3f}/{S['i'][1]:.3f}/{S['i'][2]:.3f}  {S['status']}")
