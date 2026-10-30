import cv2,numpy as np,sys,os,pickle,random,csv,glob
sys.path.insert(0,os.path.expanduser('~/BLSF-Lane-Detection/scripts'))
from blsf_eval import geometry as geo, evaluate as ev, evaluate_image as ei
import devrun
from sidefeat import collect
cfg,calib,sub,cond,out,seed=sys.argv[1:7]
R=collect(cfg,calib,sub); sel=[r for r in R if eval(cond)]
random.seed(int(seed)); sel=random.sample(sel,min(6,len(sel)))
it,mp=devrun.stage(sub); I={i.key:i for i in it}; tiles=[]
for r in sel:
    i=I[r['key']]; H,w,h=geo.load_homography_yml(f'calib/{i.group}_{calib}.yml'); Hi=ei.bev_to_image(H,w,h)
    im=cv2.imread(str(i.image))
    poly=geo.warp_points(Hi,np.array([[0,0],[w-1,0],[w-1,h-1],[0,h-1]],float)); cv2.polylines(im,[np.round(poly).astype(np.int32)],True,(255,255,0),1)
    gt=ei.gt_ego_indices(i.lanes,H,w,h,ev.EvalParams())
    for s in ('left','right'):
        if gt[s] is not None: cv2.polylines(im,[np.round(np.array(i.lanes[gt[s]])).astype(np.int32)],False,(0,0,255),2)
    y=np.arange(h,dtype=float); x=r['a']*y*y+r['b']*y+r['c']; p=geo.warp_points(Hi,np.stack([x,y],1)); p=p[np.isfinite(p).all(1)]
    cv2.polylines(im,[np.round(p).astype(np.int32)],False,(0,255,0),2)
    cv2.putText(im,f"{r['key'][-28:]} {r['side']} inl {r['inl']}/{r['npts']} b {r['b']:.2f}",(10,30),0,0.8,(0,255,255),2)
    yy=int(np.nanmin(poly[:,1]))-40
    tiles.append(cv2.resize(im[max(0,yy):min(590,yy+260)],(820,int(820*min(260,590-max(0,yy))/1640))))
H0=max(t.shape[0] for t in tiles); tiles=[cv2.copyMakeBorder(t,0,H0-t.shape[0],0,0,0) for t in tiles]
cv2.imwrite(os.path.expanduser(f'~/mnt/BLSF/_claude_tmp/{out}'),np.vstack([np.hstack(tiles[k:k+2]) for k in range(0,len(tiles),2)]))
