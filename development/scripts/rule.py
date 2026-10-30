import numpy as np,itertools,sys
from sidefeat import collect
def f1(rows,rule):
    tp=fp=fn=0
    for r in rows:
        keep=r['valid'] and rule(r)
        if keep:
            if r['ok']: tp+=1
            else: fp+=1; fn+=r['hasgt']
        else: fn+=r['hasgt']
    return 2*tp/(2*tp+fp+fn), tp/(tp+fp) if tp+fp else 0, tp/(tp+fn)
def mk(fmin,bmax,inlmin,fmin_single):
    def rule(r):
        fr=r['inl']/max(1,r['npts'])
        if abs(r['b'])>bmax or r['inl']<inlmin: return False
        return fr>=(fmin if r['other_valid'] else fmin_single)
    return rule
A=collect('v2s_with','h05','val3'); B=collect('v2s_with','h05','tr')
print('base val3 %.3f/%.3f/%.3f'%f1(A,lambda r:True),' tr %.3f/%.3f/%.3f'%f1(B,lambda r:True))
res=[]
for p in itertools.product([0,0.2,0.3,0.4,0.5],[9,0.6,0.4,0.3,0.2],[0,40,80,120],[0,0.3,0.4,0.5,0.6,0.7]):
    res.append((f1(A,mk(*p))[0],p))
res.sort(reverse=True)
for s,p in res[:8]: print('val3 %.3f'%s,p,' tr F1/P/R %.3f/%.3f/%.3f'%f1(B,mk(*p)))
