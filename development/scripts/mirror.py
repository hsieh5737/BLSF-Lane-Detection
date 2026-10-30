import os, shutil, time, sys
src=os.path.expanduser('~/mnt/BLSF/CULane_dev'); dst=os.path.expanduser('~/devdata')
val=[l.strip().lstrip('/') for l in open(f'{src}/dev_val.txt') if l.strip()]
tr=[l.strip().lstrip('/') for l in open(f'{src}/dev_train_sample.txt') if l.strip()]
keys=val[::3]+[k for k in tr if not k.startswith('driver_23_')]
if len(sys.argv)>1 and sys.argv[1]=='all': keys+=val
if len(sys.argv)>1 and sys.argv[1]=='hold': keys=[k for i,k in enumerate(val) if i%3]
t0=time.time(); n=0
for k in keys:
    for f in (k, k[:-4]+'.lines.txt'):
        d=f'{dst}/{f}'
        if os.path.exists(d): continue
        os.makedirs(os.path.dirname(d),exist_ok=True); shutil.copyfile(f'{src}/{f}',d+'.part'); os.replace(d+'.part',d); n+=1
    if time.time()-t0>155: break
print(n,'copied; done' if time.time()-t0<=155 else 'more to do')
