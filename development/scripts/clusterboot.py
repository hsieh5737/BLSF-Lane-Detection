import pickle,numpy as np,sys,os
W=sys.argv[1]; OTH=sys.argv[2:]
def load(c,sub): return {f['key']:f for f in pickle.load(open(f'scores/{c}__h05__{sub}.pkl','rb'))}
def f1(c): return 2*c[...,0]/np.maximum(2*c[...,0]+c[...,1]+c[...,2],1)
def boot(A,B,clusters,iters=2000,seed=20261029):
    rng=np.random.default_rng(seed); u,inv=np.unique(clusters,return_inverse=True)
    CA=np.zeros((len(u),3)); CB=np.zeros((len(u),3)); np.add.at(CA,inv,A); np.add.at(CB,inv,B)
    idx=rng.integers(0,len(u),size=(iters,len(u)))
    d=f1(CA[idx].sum(1))-f1(CB[idx].sum(1))
    return np.percentile(d,[2.5,97.5]), len(u)
for sub in ('valh','val3','tr'):
    a=load(W,sub)
    for other in OTH:
        b=load(other,sub); k=sorted(a)
        for m in ('b','i'):
            A=np.array([a[x][m] for x in k]); B=np.array([b[x][m] for x in k])
            d=f1(A.sum(0))-f1(B.sum(0))
            fr,_=boot(A,B,np.array(k))
            cl,n=boot(A,B,np.array(['/'.join(x.split('/')[:2]) for x in k]))
            print(f'{sub:5s} with-{other:11s} {"BEV" if m=="b" else "IMG"} dF1 {d:+.3f}  frame CI [{fr[0]:+.3f},{fr[1]:+.3f}]  clip CI [{cl[0]:+.3f},{cl[1]:+.3f}] ({n} clips)')
