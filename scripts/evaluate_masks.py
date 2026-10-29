#!/usr/bin/env python3
"""Diagnostic micro pixel metrics only, NOT the official CULane/LLAMAS evaluator.
Requires already aligned, equal-resolution 0/255 prediction and GT masks.
Never treats unpainted negative frames as perfect F1/IoU observations.
"""
import argparse,json,pathlib
import cv2,numpy as np

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--predictions",required=True);p.add_argument("--ground_truth",required=True)
    p.add_argument("--output",required=True);a=p.parse_args()
    pred,gt=pathlib.Path(a.predictions),pathlib.Path(a.ground_truth)
    pp={x.name for x in pred.glob("*.png")};gg={x.name for x in gt.glob("*.png")}
    if pp!=gg or not pp: p.error("Exact nonempty PNG filename sets are required; no silent exclusion")
    totals=np.zeros(3,dtype=np.int64);rows=[];tn_frames=0
    for name in sorted(pp):
        x=cv2.imread(str(pred/name),0);y=cv2.imread(str(gt/name),0)
        if x is None or y is None or x.shape!=y.shape: p.error("Unreadable/mismatched mask: "+name)
        if not np.isin(x,[0,255]).all() or not np.isin(y,[0,255]).all(): p.error("Masks must contain only 0 and 255: "+name)
        x=x>0;y=y>0
        tp=int(np.count_nonzero(x&y));fp=int(np.count_nonzero(x&~y));fn=int(np.count_nonzero(~x&y))
        totals += [tp,fp,fn]
        tn_frames+=int(not x.any() and not y.any())
        rows.append({"frame":name,"tp":tp,"fp":fp,"fn":fn})
    tp,fp,fn=map(int,totals)
    ratio=lambda n,d:n/d if d else None
    result={"protocol":"diagnostic_micro_pixels_v1","official_benchmark":False,
      "frames":len(rows),"both_empty_frames":tn_frames,"tp":tp,"fp":fp,"fn":fn,
      "precision":ratio(tp,tp+fp),"recall":ratio(tp,tp+fn),
      "f1":ratio(2*tp,2*tp+fp+fn),"iou":ratio(tp,tp+fp+fn),"per_frame":rows}
    pathlib.Path(a.output).write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k!="per_frame"}))
if __name__=="__main__":main()
