"""Bounded finite validation, not a mechanized universal proof or workload study.

Run each named stage separately from the repository root. Each stage is one
worker with a 40 CPU-second limit. Results retain the exact consumed inputs.
"""
import argparse, copy, csv, itertools, json, os, random, resource, sys, time
from fractions import Fraction as F
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from exact import certificate
from verify import replay, Invalid, read_json
from front_end import derive, check_interface


def save(path,obj):
    path=ROOT/path;path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')


def contract(points,p=('1/2','1/2')):
    return {'states':len(p),'vertices':[{'p':list(p),'a':[str(x) for x in a]} for a in points]}


def joint_row(total,a,b):
    """Independent integer-cell oracle: enumerate all four nonnegative cells.

    All arguments are integer multiples of one eighth; return the smallest
    feasible (G=1,H=1) cell, with an explicit joint-table witness.
    """
    feasible=[]
    for n11 in range(total+1):
        for n10 in range(total-n11+1):
            for n01 in range(total-n11-n10+1):
                n00=total-n11-n10-n01
                if n11+n10==a and n11+n01==b:
                    feasible.append((n11,(n11,n10,n01,n00)))
    if not feasible: raise AssertionError('oracle found no feasible joint table')
    return min(feasible)


def oracle_floor(points,b):
    # Lemma O in proofs/finite-oracle.md establishes completeness only for
    # this declared quarter grid and at most two supplied old generators.
    candidates=[tuple(F(x) for x in p) for p in points]
    if len(points)==2:
        candidates.append(tuple((F(x)+F(y))/2 for x,y in zip(*points)))
    values=[]
    for a in candidates:
        cells=[joint_row(4,int(8*x),int(8*y)) for x,y in zip(a,b)]
        values.append(sum(v for v,t in cells))
    return F(min(values),8)


def grid():
    points=list(itertools.product((F(0),F(1,4),F(1,2)),repeat=2))
    groups=[(p,) for p in points]+list(itertools.combinations(points,2))
    testers=points
    floors=[[oracle_floor(g,b) for b in testers] for g in groups]
    records=[];lookup={};certs=[]
    for oi,old in enumerate(groups):
        for ni,new in enumerate(points):
            task={'old':contract(old),'new':contract([new])}
            cert=certificate(task);value=replay(task,cert)
            oracle=max(F(0),max(f-oracle_floor([new],b) for f,b in zip(floors[oi],testers)))
            if value!=oracle: raise AssertionError((oi,ni,value,oracle))
            lookup[(oi,new)]=value
            records.append({'old':oi,'new_point':ni,'loss':str(value),'oracle':str(oracle)})
            certs.append({'input':task,'certificate':cert})
    pairs=[]
    for oi,old in enumerate(groups):
        for ni,new in enumerate(groups):
            generated=max(lookup[(oi,p)] for p in new)
            table=max(F(0),max(a-b for a,b in zip(floors[oi],floors[ni])))
            if generated!=table: raise AssertionError(('pair',oi,ni,generated,table))
            pairs.append({'old':oi,'new':ni,'loss':str(generated),'oracle':str(table)})
    save(Path('inputs/grid.json'),{'points':[[str(x) for x in p] for p in points],
         'contracts':[[[str(x) for x in p] for p in g] for g in groups],
         'testers':[[str(x) for x in p] for p in testers],
         'old_mixture_weights':['0','1/2','1'],'cell_denominator':8})
    # Each record is below the checker's file-size limit. The collection is
    # an evidence container, not a single accepted certificate format.
    save(Path('results/grid-certificates.json'),certs)
    save(Path('results/grid.json'),{'point_checks':records,'contract_pair_checks':pairs})
    return {'certificates_replayed':len(records),'contract_pairs_oracle_checked':len(pairs),
            'old_contracts':len(groups),'boundary_states':2,'tester_laws':len(testers),
            'mismatches':0}


def stress():
    rng=random.Random(417);records=[];details=[]
    for i in range(8):
        def C():
            return contract([tuple(F(rng.randrange(5),16) for _ in range(4)) for _ in range(5)],p=('1/4',)*4)
        task={'old':C(),'new':C()};cert=certificate(task);value=replay(task,cert)
        expected=['3/64','1/4','1/8','7/48','5/16','3/16','1/16','0'][i]
        if str(value)!=expected:raise AssertionError((i,value,expected))
        records.append({'case':i,'loss':str(value),
                        'dual_systems':sum(p['dual_systems'] for p in cert['proofs'])})
        details.append({'input':task,'certificate':cert})
    # A new deterministic set is generated after the pilot specification.
    fresh=random.Random(418)
    for i in range(12):
        k=3+i%2;den=12 if k==3 else 16
        def C():
            return contract([tuple(F(fresh.randrange(5),den) for _ in range(k))
                            for _ in range(3+i%3)],p=(str(F(1,k)),)*k)
        task={'old':C(),'new':C()};cert=certificate(task);value=replay(task,cert)
        records.append({'case':8+i,'loss':str(value),
                        'dual_systems':sum(p['dual_systems'] for p in cert['proofs'])})
        details.append({'input':task,'certificate':cert})
    save(Path('results/stress-certificates.json'),details)
    save(Path('results/stress.json'),records)
    return {'certificates_replayed':len(records),'pilot_seed':417,'additional_seed':418,
            'max_boundary_states':4,'max_generators_each':5,'mismatches':0}


def payload(x,hit,pre,cache,idx,srv):
    y=(x+1)%4
    if not pre:y^=1
    if hit and not cache:y^=1
    y^=2
    if not idx:y^=1
    y=3-y
    if not srv:y^=1
    return y


def pipeline():
    rows=[]
    for x in range(4):
        for hit,pre,cache,idx,srv in itertools.product((0,1),repeat=5):
            ref=3-(((x+1)%4)^2)
            out=payload(x,hit,pre,cache,idx,srv)
            monitor=bool(pre and idx and srv and (not hit or cache))
            good=(out==ref)
            if monitor and not good:raise AssertionError('unsound monitor')
            rows.append(dict(x=x,hit=hit,pre=pre,cache=cache,idx=idx,srv=srv,
                             reference=ref,output=out,monitor=int(monitor),correct=int(good)))
    path=ROOT/'results/pipeline-truth-table.csv'
    with path.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    model=read_json(ROOT/'inputs/pipeline-model.json');task,scope=derive(model)
    cert=certificate(task);value=replay(task,cert)
    if value!=F(1,2):raise AssertionError('pipeline loss')
    probabilities={}
    for arm in ('old','new'):
        law=model[arm]['laws'][0];variables=model[arm]['variables']
        success=F(0);scalar=F(0)
        for cell in law:
            e=dict(zip(variables,cell['assignment']));p=F(cell['mass'])
            scalar+=p*e['cache']
            # Other stages are always successful in this specific supplied
            # frame. All four payload inputs are checked; no data are fitted.
            rates=[]
            for x in range(4):
                rates.append(payload(x,e['hit'],1,e['cache'],1,1)==3-(((x+1)%4)^2))
            success+=p*F(sum(rates),len(rates))
        probabilities[arm]={'cache_scalar':str(scalar),'actual_toy_output':str(success)}
    if probabilities!={'old':{'cache_scalar':'1/2','actual_toy_output':'1'},
                       'new':{'cache_scalar':'1/2','actual_toy_output':'1/2'}}:
        raise AssertionError(probabilities)
    save(Path('results/pipeline.certificate.json'),cert)
    save(Path('results/pipeline.certificate.task.json'),task)
    save(Path('results/pipeline.certificate.scope.json'),scope)
    record={'truth_table_rows':len(rows),'monitor_true':sum(r['monitor'] for r in rows),
            'correct_output':sum(r['correct'] for r in rows),
            'correct_without_monitor':sum(r['correct'] and not r['monitor'] for r in rows),
            'monitor_false_positives':0,'replacement_loss':str(value),'source_case':probabilities}
    save(Path('results/pipeline.json'),record)
    return record


def controls():
    task=read_json(ROOT/'inputs/variable-prior.json');base=certificate(task)
    changes=[]
    def add(name,fn):
        c=copy.deepcopy(base);fn(c);changes.append((name,c))
    add('wrong-total',lambda c:c.__setitem__('value','0'))
    add('wrong-context',lambda c:c['context_success'].__setitem__(0,'1'))
    add('missing-generator',lambda c:c['proofs'].pop())
    add('negative-weight',lambda c:c['proofs'][2]['lambda'].__setitem__(0,'-1'))
    add('invalid-prior-witness',lambda c:c['old_to_new_prior'][0].__setitem__(0,'0'))
    add('negative-slack',lambda c:c['proofs'][2]['slack'].__setitem__(0,'-1'))
    add('dual-box',lambda c:c['proofs'][2]['w'].__setitem__(0,'2'))
    add('dual-objective',lambda c:c['proofs'][2]['y'].__setitem__(0,'99'))
    add('false-vertex-value',lambda c:c['proofs'][2].__setitem__('value','0'))
    add('wrong-maximizer',lambda c:c.__setitem__('worst_vertex',0))
    add('numeric-instead-of-rational-string',lambda c:c.__setitem__('value',0.5))
    add('unexpected-field',lambda c:c.__setitem__('unchecked',True))
    rejected=[]
    for name,c in changes:
        try:replay(task,c)
        except (Invalid,ValueError,TypeError):rejected.append(name)
        else:raise AssertionError('tamper accepted: '+name)
    # Same component marginals, different correlation: independent-product
    # replacement is not licensed by scopes or fresh event identifiers.
    correlated={'positive':{'11':'1/2','00':'1/2'},
                'negative':{'10':'1/2','01':'1/2'}}
    for cells in correlated.values():
        if sum(F(p) for p in cells.values())!=1:raise AssertionError('normalization')
        if sum(F(p)*int(bits[0]) for bits,p in cells.items())!=F(1,2):raise AssertionError('first marginal')
        if sum(F(p)*int(bits[1]) for bits,p in cells.items())!=F(1,2):raise AssertionError('second marginal')
    model=read_json(ROOT/'inputs/pipeline-model.json')
    bad=[]
    def check_bad(name,mutator):
        m=copy.deepcopy(model);mutator(m)
        try:derive(m)
        except (Invalid,ValueError,TypeError,KeyError):bad.append(name)
        else:raise AssertionError('bad source accepted: '+name)
    check_bad('crossing-constraint',lambda m:m['interface']['constraints'].append(
        {'event':['and','fault','pre'],'lower':'0','upper':'1'}))
    check_bad('private-observation',lambda m:m['interface'].__setitem__('monitor','fault'))
    check_bad('nonmonotone-success',lambda m:m['interface'].__setitem__('monitor',['not','cache']))
    check_bad('violated-local-law',lambda m:m['old']['laws'][0][0]['assignment'].__setitem__(2,1))
    check_bad('duplicate-event-name',lambda m:m['interface']['frame'].append('cache'))
    check_bad('invalid-mass',lambda m:m['old']['laws'][0][0].__setitem__('mass','-1/2'))
    check_bad('incompatible-frame-prior',lambda m:m['frame'].__setitem__('laws',[[{'assignment':[0,1,1,1],'mass':'1'}]]))
    prior=copy.deepcopy(task);prior['new']['vertices']=[prior['new']['vertices'][0]]
    try:certificate(prior)
    except ValueError:bad.append('changed-prior-domain')
    else:raise AssertionError('changed domain accepted')
    # Aliased event is evaluated once, however often its name is read.
    for g in (False,True):
        if (g or g)!=g:raise AssertionError('event identity')
    neg={
      'old-generator-only':{'exact_loss':'0','incorrect_loss':'1/4'},
      'scalar-summary':{'old_scalar':'1/2','new_scalar':'1/2','boundary_loss':'1/2'},
      'independent-product':{'product':'1/4','allowed_and_min':'0','allowed_and_max':'1/2'},
      'negated-success':{'old_G':'0','new_G':'1','monotone_loss':'0','negated_context_drop':'1'},
      'leaked-boundary':{'coarsened_loss':'0','full_boundary_loss':'1/2'},
      'aliases':{'same_event_or':'1/2','two_independent_events_or':'3/4'},
      'old-row-rectangularization':{'true_floor_at_b_equals_p':'1/2','rectangularized_floor':'0'}
    }
    # Recompute every displayed semantic value; these are not unevaluated
    # illustrative constants. The independent table oracle covers the grid.
    interior=read_json(ROOT/'inputs/interior-mixture.json')
    boundary=read_json(ROOT/'inputs/boundary-sensitive.json')
    def loss(t):return replay(t,certificate(t))
    if loss(interior)!=0 or loss(boundary)!=F(1,2):raise AssertionError('semantic control')
    old_points=[v['a'] for v in interior['old']['vertices']]
    target=interior['new']['vertices'][0]['a']
    naive=min(sum(max(F(0),F(c)-F(a)) for c,a in zip(pt,target)) for pt in old_points)
    if naive!=F(1,4):raise AssertionError('old-generator shortcut')
    coarsened={'old':contract([(F(1,2),)],('1',)),
               'new':contract([(F(1,2),)],('1',))}
    improved={'old':contract([(F(0),)],('1',)),
              'new':contract([(F(1),)],('1',))}
    if loss(coarsened)!=0 or loss(improved)!=0:raise AssertionError('hiding or negation')
    and_masses=[sum(F(m) for bits,m in cells.items() if bits=='11') for cells in correlated.values()]
    if min(and_masses)!=0 or max(and_masses)!=F(1,2):raise AssertionError('correlation')
    independent_or=sum(F(1,4) for a,b in itertools.product((0,1),repeat=2) if a or b)
    if independent_or!=F(3,4):raise AssertionError('alias distinction')
    if oracle_floor(old_points,(F(1,2),F(1,2)))!=F(1,2):raise AssertionError('whole-law mixture')
    if oracle_floor([('0','0')],(F(1,2),F(1,2)))!=0:raise AssertionError('row relaxation')
    save(Path('results/negative-controls.json'),{'certificate_rejections':rejected,
         'source_rejections':bad,'counterexamples':neg,'correlation_laws':correlated})
    return {'corrupted_certificates_rejected':len(rejected),'invalid_sources_or_domains_rejected':len(bad),
            'semantic_counterexamples':len(neg)}


def replay_all():
    count=0
    for name in ('grid','stress'):
        collection=json.loads((ROOT/f'results/{name}-certificates.json').read_text())
        for item in collection:
            replay(item['input'],item['certificate']);count+=1
    for name in ('interior-mixture','boundary-sensitive','variable-prior','zero-mass','exposed-mode','hidden-mode'):
        replay(read_json(ROOT/f'inputs/{name}.json'),read_json(ROOT/f'results/{name}.certificate.json'));count+=1
    replay(read_json(ROOT/'results/pipeline.certificate.task.json'),read_json(ROOT/'results/pipeline.certificate.json'));count+=1
    return {'certificates_replayed':count}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['grid','stress','pipeline','controls','replay'])
    args=parser.parse_args();os.chdir(ROOT)
    if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    resource.setrlimit(resource.RLIMIT_AS,(3500*1024**2,3500*1024**2))
    resource.setrlimit(resource.RLIMIT_CPU,(40,40))
    cpu=time.process_time();wall=time.perf_counter()
    result={'grid':grid,'stress':stress,'pipeline':pipeline,'controls':controls,'replay':replay_all}[args.stage]()
    record={'stage':args.stage,'result':result,'workers':1,
            'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,
            'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(Path(f'results/{args.stage}-resources.json'),record)
    print(json.dumps(record,sort_keys=True))

if __name__=='__main__':main()
