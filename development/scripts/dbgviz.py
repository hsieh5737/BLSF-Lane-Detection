import cv2,numpy as np,glob,os,sys,pickle,random,subprocess,shutil
sys.path.insert(0,os.path.expanduser('~/BLSF-Lane-Detection/scripts'))
from blsf_eval import geometry as geo, evaluate as ev, datasets
cfg,calib,sub,cond,out,seed=sys.argv[1:7]
fr=pickle.load(open(f'scores/{os.path.basename(cfg)[:-5]}__{calib}__{sub}.pkl','rb'))
sel=[f for f in fr if eval(cond)]
random.seed(int(seed)); sel=random.sample(sel,min(6,len(sel)))
shutil.rmtree('dbg_in',True); shutil.rmtree('dbg_out',True); os.makedirs('dbg_in')
rows=[]
for f in sel:
    g=f['group']; k=f['key']; nm=k.replace('/','__')
    os.makedirs(f'dbg_in/{nm[:-4]}'); os.symlink(os.path.expanduser('~/devdata/')+k,f'dbg_in/{nm[:-4]}/{nm}')
    subprocess.run([os.path.expanduser('~/BLSF-Lane-Detection/build/blsf_lane'),'--config',cfg,'--input_dir',f'dbg_in/{nm[:-4]}','--homography',f'calib/{g}_{calib}.yml','--output_dir',f'dbg_out/{nm[:-4]}','--debug_dir',f'dbg_out/{nm[:-4]}/debug'],capture_output=True)
    d=glob.glob(f'dbg_out/{nm[:-4]}/debug/*')[0]
    H,w,h=geo.load_homography_yml(f'calib/{g}_{calib}.yml')
    lanes=datasets.read_culane_lines(datasets.Path(os.path.expanduser('~/devdata/')+k[:-4]+'.lines.txt'))
    gt=ev.gt_ego_lanes(lanes,H,w,h,ev.EvalParams())
    tiles=[]
    im=cv2.imread(os.path.expanduser('~/devdata/')+k)
    cv2.putText(im,f"{k[-30:]} {f['status']} iou={f['iou']}",(10,40),0,1.0,(0,0,255),2)
    tiles.append(cv2.resize(im,(600,216)))
    for n in ('01_bev','04_binary','06_seg_after','09_windows','10_overlay'):
        t=cv2.imread(f'{d}/{n}.png')
        if n=='10_overlay':
            for s in ('left','right'):
                if gt[s] is not None: t[gt[s]>0]=(0.5*t[gt[s]>0]+[0,0,127]).astype(np.uint8)
        tiles.append(cv2.resize(t,(162,216)))
    rows.append(np.hstack(tiles))
cv2.imwrite(os.path.expanduser(f'~/mnt/BLSF/_claude_tmp/{out}'),np.vstack(rows))
