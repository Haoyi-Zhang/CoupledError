"""One-worker discriminating pilot. Run from artifact/."""
import json,sys,time,resource,os
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from exact import certificate,deficit
from verify import replay

def C(vs):
    return {'states':len(vs[0][0]),'vertices':[{'p':list(p),'a':list(a)} for p,a in vs]}

cases={
 'interior-mixture':{'old':C([(('1/2','1/2'),('1/2','0')),(('1/2','1/2'),('0','1/2'))]),
                     'new':C([(('1/2','1/2'),('1/4','1/4'))])},
 'boundary-sensitive':{'old':C([(('1/2','1/2'),('1/2','0'))]),
                      'new':C([(('1/2','1/2'),('0','1/2'))])},
 'variable-prior':{'old':C([(('1','0'),('1','0')),(('0','1'),('0','1'))]),
                   'new':C([(('1','0'),('1','0')),(('0','1'),('0','1')),(('1/2','1/2'),('1/4','1/4'))])},
 'zero-mass':{'old':C([(('1','0'),('3/4','0'))]),'new':C([(('1','0'),('1/2','0'))])}
}
expected={'interior-mixture':F(0),'boundary-sensitive':F(1,2),'variable-prior':F(1,2),'zero-mass':F(1,4)}
if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(3500*1024**2,3500*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(40,40))
start=time.process_time(); wall=time.perf_counter();results=[]
for name,task in cases.items():
 cert=certificate(task);val=replay(task,cert)
 if val!=expected[name]:raise AssertionError((name,val))
 Path('inputs').mkdir(exist_ok=True);Path('results').mkdir(exist_ok=True)
 Path(f'inputs/{name}.json').write_text(json.dumps(task,indent=2)+'\n')
 Path(f'results/{name}.certificate.json').write_text(json.dumps(cert,indent=2)+'\n')
 results.append({'case':name,'loss':str(val),'new_vertices':len(task['new']['vertices'])})
# Negative control: checking only OLD generators misses the feasible midpoint.
naive=min(sum(max(F(0),F(c)-F(a)) for c,a in zip(v['a'],cases['interior-mixture']['new']['vertices'][0]['a'])) for v in cases['interior-mixture']['old']['vertices'])
if not naive>expected['interior-mixture']:raise AssertionError('negative control failed')
record={'workers':1,'cases':results,'negative_control_old_vertex_only':str(naive),
        'cpu_seconds':time.process_time()-start,'wall_seconds':time.perf_counter()-wall,
        'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'status':'finite exact checks passed; not a general mechanized proof'}
Path('results/pilot.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record,indent=2))
