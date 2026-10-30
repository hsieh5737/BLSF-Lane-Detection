import pickle,os,sys,numpy as np
sys.path.insert(0,os.path.expanduser('~/BLSF-Lane-Detection/scripts'))
from blsf_eval import geometry as geo, evaluate as ev
import devrun
def gt_curv(sub,calib='h05'):
    pk=f'gtcurv_{sub}_{calib}.pkl'
    if os.path.exists(pk): return pickle.load(open(pk,'rb'))
    it,_=devrun.stage(sub); Hs={}; out={}
    for i in it:
        if i.group not in Hs: Hs[i.group]=geo.load_homography_yml(f'calib/{i.group}_{calib}.yml')
        H,w,h=Hs[i.group]; gt=ev.gt_ego_lanes(i.lanes,H,w,h,ev.EvalParams()); A=[]
        for s in ('left','right'):
            if gt[s] is None: continue
            rows=geo.covered_rows(gt[s]); x=np.array([np.flatnonzero(gt[s][y]).mean() for y in rows])
            A.append(abs(np.polyfit(rows,x,2)[0]))
        out[i.key]=max(A) if A else None
    pickle.dump(out,open(pk,'wb')); return out
if __name__=='__main__':
    cfgs=sys.argv[1:]
    for sub in ('val3','tr'):
        C=gt_curv(sub)
        v=np.array([a for a in C.values() if a is not None]); print(sub,'GT |a| pct 50/90/97/99:',np.percentile(v,[50,90,97,99]).round(5), 'n>3e-4:',(v>3e-4).sum(),'n>8e-4',(v>8e-4).sum())
        for c in cfgs:
            fr=pickle.load(open(f'scores/{c}__h05__{sub}.pkl','rb'))
            for lo,hi in ((0,3e-4),(3e-4,1)):
                t=np.array([f['b'] for f in fr if C[f['key']] is not None and lo<=C[f['key']]<hi]).sum(0)
                ti=np.array([f['i'] for f in fr if C[f['key']] is not None and lo<=C[f['key']]<hi]).sum(0)
                print('   %-26s |a| in [%g,%g): BEV F1 %.3f IMG F1 %.3f'%(c,lo,hi,2*t[0]/(2*t[0]+t[1]+t[2]),2*ti[0]/(2*ti[0]+ti[1]+ti[2])))
