import csv,glob,numpy as np,sys,os,pickle
sys.path.insert(0,os.path.expanduser('~/BLSF-Lane-Detection/scripts'))
from blsf_eval import geometry as geo, evaluate as ev
import devrun
cfg,calib,sub=sys.argv[1:4]
it,mp=devrun.stage(sub); preds={}
for f in glob.glob(f'runs/{cfg}__{calib}/{sub}/*/b*/predictions.csv'):
    for r in csv.DictReader(open(f)): preds[mp[r['image'].split('/')[-1]]]=r
Hs={}; stats={}
for W in (65,70,75,80):
    stats[W]=[0,0,0]
for i in it:
    r=preds[i.key]
    if r['status']!='partial': continue
    if i.group not in Hs: Hs[i.group]=geo.load_homography_yml(f'calib/{i.group}_{calib}.yml')
    H,w,h=Hs[i.group]; gt=ev.gt_ego_lanes(i.lanes,H,w,h,ev.EvalParams())
    s='left' if r['left_valid']=='1' else 'right'; o='right' if s=='left' else 'left'
    if gt[o] is None: 
        for W in stats: stats[W][2]+=1
        continue
    a,b,c=(float(r[f'{s}_{k}']) for k in 'abc')
    for W in stats:
        cc=c+W if s=='left' else c-W
        iou=ev.side_iou(geo.render_poly2(a,b,cc,w,h,10),gt[o])
        stats[W][0]+=iou>=0.5; stats[W][1]+=1
for W,(hit,n,nogt) in stats.items(): print('W',W,'inferred other side correct',hit,'of',n,'GT-present; no GT on other side',nogt)
