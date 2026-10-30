# Dev-only homographies from a flat-road pinhole model fitted on train frames:
# image row v = vh + k/Z, column x = vx + X*c*k/(W*Z), W = 3.75 m lane width.
import json, sys, subprocess, os
P=json.load(open('dev_calib_params.json'))
K={'driver_23_30frame':577,'driver_161_90frame':565,'driver_182_30frame':613}
R=os.path.expanduser('~/BLSF-Lane-Detection')
img=os.path.expanduser('~/mnt/BLSF/CULane_dev')
for d,p in P.items():
    k=K[d]; vh,vx,c,hood=p['vh'],p['vx'],p['c'],p['hood']
    zh=k/(hood-vh)
    for tag,dz in (('h2',2.0),('h05',0.5)):
        Z0=zh+dz
        def pt(X,Z): return (vx+X*c*k/(3.75*Z), vh+k/Z)
        pts=[pt(-1.875,Z0+15),pt(1.875,Z0+15),pt(1.875,Z0),pt(-1.875,Z0)]
        s=';'.join('%.2f,%.2f'%q for q in pts)
        first=sorted(os.listdir(f'{img}/{d}'))[0]; fr=sorted(f for f in os.listdir(f'{img}/{d}/{first}') if f.endswith('.jpg'))[0]
        out=f'calib/{d}_{tag}.yml'
        subprocess.run([sys.executable,f'{R}/scripts/make_homography.py','--image',f'{img}/{d}/{first}/{fr}','--points',s,
                        '--rect_w_m','3.75','--rect_l_m','15','--out',out,'--preview',f'calib/{d}_{tag}.png'],check=True,capture_output=True)
        print(d,tag,'Z_hood %.1f Z0 %.1f rows %.0f..%.0f'%(zh,Z0,pts[2][1],pts[0][1]))
