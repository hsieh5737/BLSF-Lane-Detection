import cv2,numpy as np,glob,os,sys,pickle,random,subprocess,shutil,csv
sys.path.insert(0,os.path.expanduser('~/BLSF-Lane-Detection/scripts'))
from blsf_eval import geometry as geo, evaluate as ev, datasets
cfg,calib,sub,cond,out,seed=sys.argv[1:7]
fr=pickle.load(open(f'scores/{os.path.basename(cfg)[:-5]}__{calib}__{sub}.pkl','rb'))
sel=[f for f in fr if eval(cond)]
random.seed(int(seed)); sel=random.sample(sel,min(8,len(sel)))
shutil.rmtree('dbg_in',True); shutil.rmtree('dbg_out',True); os.makedirs('dbg_in')
cols=[]
for f in sel:
    g=f['group']; k=f['key']; nm=k.replace('/','__')
    os.makedirs(f'dbg_in/{nm[:-4]}'); os.symlink(os.path.expanduser('~/devdata/')+k,f'dbg_in/{nm[:-4]}/{nm}')
    subprocess.run([os.path.expanduser('~/BLSF-Lane-Detection/build/blsf_lane'),'--config',cfg,'--input_dir',f'dbg_in/{nm[:-4]}','--homography',f'calib/{g}_{calib}.yml','--output_dir',f'dbg_out/{nm[:-4]}','--debug_dir',f'dbg_out/{nm[:-4]}/debug'],capture_output=True)
    d=glob.glob(f'dbg_out/{nm[:-4]}/debug/*')[0]
    H,w,h=geo.load_homography_yml(f'calib/{g}_{calib}.yml')
    lanes=datasets.read_culane_lines(datasets.Path(os.path.expanduser('~/devdata/')+k[:-4]+'.lines.txt'))
    gt=ev.gt_ego_lanes(lanes,H,w,h,ev.EvalParams())
    bev=cv2.imread(f'{d}/01_bev.png'); ov=bev.copy()
    for s in ('left','right'):
        if gt[s] is not None: ov[gt[s]>0]=(0,0,255)
    r=list(csv.DictReader(open(glob.glob(f'dbg_out/{nm[:-4]}/predictions.csv')[0])))[0]
    for s in ('left','right'):
        if r[f'{s}_valid']=='1':
            a,b,c=(float(r[f'{s}_{q}']) for q in 'abc'); y=np.arange(h); x=a*y*y+b*y+c
            pts=np.stack([x,y],1).round().astype(np.int32)
            cv2.polylines(ov,[pts.reshape(-1,1,2)],False,(0,255,0),1)
    win=cv2.imread(f'{d}/09_windows.png'); seg=cv2.imread(f'{d}/06_seg_after.png')
    col=np.vstack([bev,seg,win,ov]); cv2.putText(col,k[-24:-4],(2,12),0,0.35,(0,255,255),1); cv2.putText(col,str(f['iou']),(2,24),0,0.35,(0,255,255),1)
    cols.append(col)
cv2.imwrite(os.path.expanduser(f'~/mnt/BLSF/_claude_tmp/{out}'),np.hstack(cols))
