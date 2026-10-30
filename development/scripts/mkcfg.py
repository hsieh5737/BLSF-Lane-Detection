import sys,re
base,out=sys.argv[1],sys.argv[2]; s=open(base).read()
for kv in sys.argv[3:]:
    sec,key,val=re.match(r'(\w+)\.(\w+)=(.*)',kv).groups()
    m=re.search(rf'^{sec}:\n((?:[ \t]+.*\n|\n)*)',s,re.M)
    body=m.group(1)
    if re.search(rf'^\s+{key}:',body,re.M):
        body2=re.sub(rf'^(\s+){key}:.*$',rf'\g<1>{key}: {val}',body,flags=re.M)
    else:
        body2=body.rstrip('\n')+f'\n  {key}: {val}\n'
    s=s[:m.start(1)]+body2+s[m.end(1):]
open(out,'w').write(s)
