#!/usr/bin/env python3
"""Run corrected pipeline, retain input/config/executable hashes and raw outputs.
This is a new-run manifest; it does not authenticate historical experiments.
"""
import argparse, hashlib, json, os, pathlib, platform, subprocess, datetime

def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser()
    for a in ("binary","config","input_dir","homography","output_dir"):p.add_argument("--"+a,required=True)
    a=p.parse_args()
    out=pathlib.Path(a.output_dir).resolve()
    if out.exists() and any(out.iterdir()):p.error("output_dir must be empty, preserving earlier runs")
    out.mkdir(parents=True,exist_ok=True)
    inputs=pathlib.Path(a.input_dir).resolve()
    if inputs == out or inputs in out.parents:p.error("output_dir must be outside input_dir")
    binary=pathlib.Path(a.binary).resolve()
    config=pathlib.Path(a.config).resolve();homography=pathlib.Path(a.homography).resolve()
    files=sorted(x for x in inputs.iterdir() if x.suffix.lower() in (".png",".jpg",".jpeg",".bmp",".tif",".tiff") and x.is_file())
    if not files:p.error("No images")
    if len({x.stem for x in files}) != len(files):p.error("Image stems must be unique to avoid debug-output collisions")
    cmd=[str(binary),"--config",str(config),"--input_dir",str(inputs),"--homography",str(homography),"--output_dir",str(out),"--debug_dir",str(out/"debug")]
    repo=pathlib.Path(__file__).resolve().parents[1]
    code=[x for d in ("src","configs","scripts") for x in sorted((repo/d).glob("*")) if x.is_file()]
    manifest={"schema":"blsf-new-run-v1","historical_reproduction":False,"command":cmd,
      "started_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
      "platform":platform.platform(),"machine":platform.machine(),"processor":platform.processor(),
      "binary_sha256":sha(binary),"config_sha256":sha(config),"homography_sha256":sha(homography),
      "input_files":[{"name":str(x.relative_to(inputs)),"sha256":sha(x)} for x in files],
      "source_files":[{"name":str(x.relative_to(repo)),"sha256":sha(x)} for x in code],
      "timing_scope":"run_pipeline including debug-image construction; excludes image read, debug-file write and output CSV; not an ARM benchmark"}
    (out/"config_used.yaml").write_bytes(config.read_bytes())
    (out/"homography_used.yml").write_bytes(homography.read_bytes())
    with open(out/"stdout.log","w") as log,open(out/"stderr.log","w") as err:
        r=subprocess.run(cmd,stdout=log,stderr=err)
    manifest["exit_code"]=r.returncode
    manifest["ended_utc"]=datetime.datetime.now(datetime.timezone.utc).isoformat()
    manifest["output_files"]=[{"name":str(x.relative_to(out)),"sha256":sha(x)} for x in sorted(out.rglob("*")) if x.is_file()]
    (out/"manifest.json").write_text(json.dumps(manifest,indent=2))
    if r.returncode:raise SystemExit(r.returncode)
    import csv
    rows=list(csv.DictReader(open(out/"predictions.csv")))
    if len(rows)!=len(files):raise SystemExit("Prediction count mismatch; inspect logs")
    print(json.dumps({"frames":len(rows),"ok":sum(x["ok"]=="1" for x in rows),"manifest":str(out/"manifest.json")}))
if __name__=="__main__":main()
