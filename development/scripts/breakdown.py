import csv,glob,numpy as np,sys,os,pickle
sys.path.insert(0,os.path.expanduser('~/BLSF-Lane-Detection/scripts'))
from blsf_eval import geometry as geo, evaluate as ev
import devrun
def run(cfg,calib,sub):
    it,mp=devrun.stage(sub); preds={}
    for f in glob.glob(f'runs/{cfg}__{calib}/{sub}/*/b*/predictions.csv'):
        for r in csv.DictReader(open(f)): preds[mp[r['image'].split('/')[-1]]]=r
    Hs={}; cat={'correct':0,'near<10':0,'off10-60':0,'neighbor>60':0,'missing':0,'pred_noGT':0}; nearfar=[]
    for i in it:
        if i.group not in Hs: Hs[i.group]=geo.load_homography_yml(f'calib/{i.group}_{calib}.yml')
        H,w,h=Hs[i.group]; r=preds[i.key]; gt=ev.gt_ego_lanes(i.lanes,H,w,h,ev.EvalParams())
        for s in ('left','right'):
            v=r[f'{s}_valid']=='1'
            if gt[s] is None:
                cat['pred_noGT']+=v; continue
            if not v: cat['missing']+=1; continue
            a,b,c=(float(r[f'{s}_{k}']) for k in 'abc'); rows=geo.covered_rows(gt[s])
            gx=np.array([np.flatnonzero(gt[s][y]).mean() for y in rows]); d=a*rows**2+b*rows+c-gx
            pm=geo.render_poly2(a,b,c,w,h,10); iou=ev.side_iou(pm,gt[s])
            if iou>=0.5: cat['correct']+=1
            else:
                m=np.median(np.abs(d)); cat['near<10' if m<10 else 'off10-60' if m<60 else 'neighbor>60']+=1
    return cat
if __name__=='__main__':
    for c in sys.argv[3:]: print(c,sys.argv[2],run(c,sys.argv[1],sys.argv[2]))
