# Vanishing point per frame from the GT ego lanes (dev data only); resumable.
import sys, os, json, time, numpy as np
root=os.path.expanduser('~/mnt/BLSF/CULane_dev'); out=os.path.expanduser('~/dev/vp.jsonl')
done=set()
if os.path.exists(out):
    done={json.loads(l)['key'] for l in open(out)}
keys=[l.strip().lstrip('/') for f in ('dev_val.txt','dev_train_sample.txt') for l in open(f'{root}/{f}') if l.strip()]
t0=time.time(); fo=open(out,'a'); n=0
for k in keys:
    if k in done: continue
    if time.time()-t0>150: break
    lanes=[]
    for l in open(f'{root}/{k[:-4]}.lines.txt'):
        v=np.array(list(map(float,l.split()))).reshape(-1,2)
        if len(v)>=4: lanes.append(v)
    rec={'key':k}
    # ego lanes: lowest point x relative to centre 820
    L=[];R=[]
    for v in lanes:
        lo=v[np.argmax(v[:,1])]
        (L if lo[0]<820 else R).append((lo[0],v))
    if L and R:
        l=max(L,key=lambda t:t[0])[1]; r=min(R,key=lambda t:t[0])[1]
        fits=[]
        for v in (l,r):
            s=v[v[:,1]>=v[:,1].max()-120]   # near part (lowest 120 rows)
            if len(s)<3: fits=None; break
            A=np.polyfit(s[:,1],s[:,0],1); res=np.abs(np.polyval(A,s[:,1])-s[:,0]).max()
            # straightness: compare with fit on whole lane
            B=np.polyfit(v[:,1],v[:,0],1); resall=np.abs(np.polyval(B,v[:,1])-v[:,0]).max()
            fits.append((A,resall))
        if fits:
            (a1,b1),r1=fits[0]; (a2,b2),r2=fits[1]
            if abs(a1-a2)>1e-6:
                y=(b2-b1)/(a1-a2); x=a1*y+b1
                rec.update(vx=x,vy=y,straight=max(r1,r2),xl=float(np.polyval([a1,b1],590)),xr=float(np.polyval([a2,b2],590)))
    fo.write(json.dumps(rec)+'\n'); n+=1
print(n,'new', len(done)+n,'of',len(keys))
