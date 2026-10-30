import csv,glob,numpy as np,sys,os,pickle
sys.path.insert(0,os.path.expanduser('~/BLSF-Lane-Detection/scripts'))
from blsf_eval import geometry as geo, evaluate as ev
import devrun
def collect(cfg,calib,sub):
    pk=f'scores/side_{cfg}__{calib}__{sub}.pkl'
    if os.path.exists(pk): return pickle.load(open(pk,'rb'))
    it,mp=devrun.stage(sub); preds={}
    for f in glob.glob(f'runs/{cfg}__{calib}/{sub}/*/b*/predictions.csv'):
        for r in csv.DictReader(open(f)): preds[mp[r['image'].split('/')[-1]]]=r
    Hs={}; rows=[]
    for i in it:
        if i.group not in Hs: Hs[i.group]=geo.load_homography_yml(f'calib/{i.group}_{calib}.yml')
        H,w,h=Hs[i.group]; r=preds[i.key]; gt=ev.gt_ego_lanes(i.lanes,H,w,h,ev.EvalParams())
        for s in ('left','right'):
            hasgt=gt[s] is not None; v=r[f'{s}_valid']=='1'; ok=0
            if v and hasgt:
                a,b,c=(float(r[f'{s}_{k}']) for k in 'abc'); ok=int(ev.side_iou(geo.render_poly2(a,b,c,w,h,10),gt[s])>=0.5)
            o=None
            rows.append(dict(key=i.key,side=s,hasgt=hasgt,valid=v,ok=ok,status=r['status'],
                a=float(r[f'{s}_a'] or 0),b=float(r[f'{s}_b'] or 0),c=float(r[f'{s}_c'] or 0),
                inl=int(r[f'{s}_inliers'] or 0),npts=int(r[f'{s}_npts'] or 0),span=int(r[f'{s}_span'] or 0),hits=int(r[f'{s}_hits'] or 0),
                other_valid=r[('right' if s=='left' else 'left')+'_valid']=='1',
                oc=float(r[('right' if s=='left' else 'left')+'_c'] or 0),ob=float(r[('right' if s=='left' else 'left')+'_b'] or 0),oa=float(r[('right' if s=='left' else 'left')+'_a'] or 0)))
    pickle.dump(rows,open(pk,'wb')); return rows
def auc(x,y):
    x=np.asarray(x,float); y=np.asarray(y); p=x[y==1]; n=x[y==0]
    if len(p)==0 or len(n)==0: return np.nan
    r=np.argsort(np.argsort(np.r_[p,n]))+1
    return (r[:len(p)].sum()-len(p)*(len(p)+1)/2)/(len(p)*len(n))
if __name__=='__main__':
    calib,sub,cfg=sys.argv[1:4]
    R=[r for r in collect(cfg,calib,sub) if r['valid']]
    y=np.array([r['ok'] for r in R])
    print(sub,cfg,'predicted sides',len(R),'correct',y.sum())
    h=300
    feats={'inl':[r['inl'] for r in R],'npts':[r['npts'] for r in R],'span':[r['span'] for r in R],'hits':[r['hits'] for r in R],
           'inl_frac':[r['inl']/max(1,r['npts']) for r in R],'|a|':[-abs(r['a']) for r in R],'|b|':[-abs(r['b']) for r in R],
           'pair':[r['other_valid'] for r in R]}
    # pair width deviation at bottom and top
    def xb(a,b,c,y): return a*y*y+b*y+c
    wd=[]; par=[]
    for r in R:
        if r['other_valid']:
            wb=abs(xb(r['a'],r['b'],r['c'],h-1)-xb(r['oa'],r['ob'],r['oc'],h-1)); wt=abs(xb(r['a'],r['b'],r['c'],0)-xb(r['oa'],r['ob'],r['oc'],0))
            wd.append(-abs(wb-75)); par.append(-abs(wb-wt))
        else: wd.append(-999); par.append(-999)
    feats['width_dev']=wd; feats['parallel']=par
    for k,v in feats.items(): print('  AUC %-10s %.3f'%(k,auc(v,y)))
