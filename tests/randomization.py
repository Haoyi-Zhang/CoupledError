"""A discriminating finite randomization/abstraction check, not a workload."""
import itertools,json,os,resource,sys,time
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from exact import certificate
from verify import replay
if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
resource.setrlimit(resource.RLIMIT_AS,(3500*1024**2,3500*1024**2))
resource.setrlimit(resource.RLIMIT_CPU,(40,40))
cpu=time.process_time();wall=time.perf_counter()
def contract(p,a):return {'states':len(p),'vertices':[{'p':[str(x) for x in p],'a':[str(x) for x in a]}]}
# Encode an AND floor as a loss to the complement-test singleton. Its floor
# under that tester is zero, so the certificate proves the old floor exactly.
def check(name,p,a,b,expected):
    task={'old':contract(p,a),'new':contract(p,[x-y for x,y in zip(p,b)])}
    cert=certificate(task);v=replay(task,cert)
    if v!=expected:raise AssertionError((name,v,expected))
    for folder,obj in [('inputs',task),('results',cert)]:
        path=ROOT/f'{folder}/{name}{".certificate" if folder=="results" else ""}.json'
        path.write_text(json.dumps(obj,indent=2)+'\n')
    return {'case':name,'floor':str(v)}
checks=[check('exposed-mode',[F(1,4)]*4,[F(1,4),F(0),F(0),F(1,4)],[F(1,8)]*4,F(1,4)),
        check('hidden-mode',[F(1,2)]*2,[F(1,4)]*2,[F(1,4)]*2,F(0))]
# Exact formula on 17 illustrative mixtures. The continuous maximum is
# proved in core.md; the grid alone does not establish it.
old=[(F(1,2),F(0)),(F(0),F(1,2))];rows=[]
for i in range(17):
    lam=F(i,16);target=(lam/2,(1-lam)/2)
    val=min(sum(max(F(0),c-a) for c,a in zip(point,target)) for point in old)
    expected=min(lam,1-lam)/2
    if val!=expected:raise AssertionError('nonconvex deficit')
    rows.append({'lambda':str(lam),'nonconvex_loss':str(val)})
if max(F(r['nonconvex_loss']) for r in rows)!=F(1,4):raise AssertionError('interior maximum')
# Two explicit laws with the SAME marginal laws on S,M,G and S,H.
# Only the first obeys fresh-mode independence of M and H conditional on S.
fresh=[];ambient=[]
for s,m,h in itertools.product((0,1),repeat=3):
    fresh.append((s,m,int(s==m),h,F(1,8)))
for s,m in itertools.product((0,1),repeat=2):
    g=int(s==m);ambient.append((s,m,g,1-g,F(1,4)))
def marginal(law,columns):
    out={}
    for row in law:
        key=tuple(row[i] for i in columns);out[key]=out.get(key,F(0))+row[-1]
    return {k:v for k,v in out.items() if v}
if marginal(fresh,(0,1,2))!=marginal(ambient,(0,1,2)):raise AssertionError('local marginal')
if marginal(fresh,(0,3))!=marginal(ambient,(0,3)):raise AssertionError('frame marginal')
fresh_floor=sum(row[-1] for row in fresh if row[2] and row[3])
ambient_floor=sum(row[-1] for row in ambient if row[2] and row[3])
if (fresh_floor,ambient_floor)!=(F(1,4),F(0)):raise AssertionError('mode distinction')
def serialize(law):return [{'S':s,'M':m,'G':g,'H':h,'mass':str(p)} for s,m,g,h,p in law]
result={'floor_certificates':checks,'mixtures':rows,'fresh_law':serialize(fresh),
        'ambient_law':serialize(ambient),'fresh_floor':str(fresh_floor),'ambient_floor':str(ambient_floor),
        'marginals_agree':True,'new_generator_only_would_report':'0','true_nonconvex_loss':'1/4'}
(ROOT/'results/randomization.json').write_text(json.dumps(result,indent=2)+'\n')
res={'stage':'randomization','workers':1,'result':{'certificates_replayed':2,'mixtures_checked':17},
     'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,
     'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
(ROOT/'results/randomization-resources.json').write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps(res))
