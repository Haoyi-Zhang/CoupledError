"""Deterministic exact validation for order-coupling and join-tree code."""
import copy
import itertools
import json
import os
import random
import resource
import sys
import tempfile
import time
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from order_common import parse_task, upward_sets
from order_run import certificate
from order_verify import Invalid, replay
import join_tree


def bool_poset(bits):
    outcomes = [''.join(x) for x in itertools.product('01', repeat=bits)]
    leq = [[int(all(int(a) <= int(b) for a,b in zip(x,y))) for y in outcomes] for x in outcomes]
    return outcomes, leq


def compositions(total, parts):
    if parts == 1:
        yield (total,); return
    for first in range(total+1):
        for rest in compositions(total-first, parts-1):
            yield (first,)+rest


def q(x, denominator):
    return str(F(x, denominator))


def random_row(rng, total, n):
    cuts = sorted(rng.randrange(total+1) for _ in range(n-1))
    points = [0]+cuts+[total]
    return [points[i+1]-points[i] for i in range(n)]


def random_task(seed):
    rng = random.Random(seed)
    bits = 1 if seed % 3 == 0 else 2
    outcomes, leq = bool_poset(bits)
    n = len(outcomes)
    k = 1 + (seed % 2)
    denominator = 6
    row_totals = [denominator] if k == 1 else [2 + (seed % 3), denominator-(2+(seed%3))]
    def gen():
        return {'mass': [[q(v, denominator) for v in random_row(rng, total, n)]
                         for total in row_totals]}
    old_count = 1 + seed % 4
    new_count = 1 + (seed//2) % 3
    return {'boundary':[f's{i}' for i in range(k)],
            'poset':{'outcomes':outcomes,'leq':leq},
            'old':{'generators':[gen() for _ in range(old_count)]},
            'new':{'generators':[gen() for _ in range(new_count)]}}


def brute_unit_deficit(a, b, leq, denominator):
    left=[];right=[]
    for i,c in enumerate(a): left += [i]*c
    for i,c in enumerate(b): right += [i]*c
    best=denominator
    for perm in set(itertools.permutations(right)):
        bad=sum(not leq[x][y] for x,y in zip(left,perm))
        best=min(best,bad)
    return best


def oracle_grid():
    outcomes, leq = bool_poset(2)
    upsets = upward_sets(tuple(tuple(bool(x) for x in row) for row in leq))
    denominator=4
    laws=list(compositions(denominator,4))
    pairs=0; mismatches=0
    distances={}
    for i,a in enumerate(laws):
        for j,b in enumerate(laws):
            pairs+=1
            upset=max([0]+[sum(a[x] for x in U)-sum(b[x] for x in U) for U in upsets])
            brute=brute_unit_deficit(a,b,leq,denominator)
            if upset != brute: mismatches += 1
            distances[(i,j)] = upset
    triangle=0
    for i in range(len(laws)):
        for j in range(len(laws)):
            for k in range(len(laws)):
                if distances[(i,k)] > distances[(i,j)]+distances[(j,k)]:
                    triangle += 1
    return {'denominator':denominator,'laws':len(laws),'ordered_pairs':pairs,
            'transport_upset_mismatches':mismatches,
            'triangle_triples':len(laws)**3,'triangle_violations':triangle}


def direct_event_gap(task):
    _,_,leq,old,new,_=parse_task(task)
    U=upward_sets(leq)
    target=new[0]
    gaps=[]
    for s in range(len(target)):
        for up in U:
            old_floor=min(sum(g[s][x] for x in up) for g in old)
            new_floor=sum(target[s][x] for x in up)
            gaps.append(old_floor-new_floor)
    return max([F(0)]+gaps)


def main():
    if hasattr(os,'sched_getaffinity'):
        os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})
    start=time.perf_counter(); cpu=time.process_time()
    retained={}
    for name in ['order-binary','order-pipeline','order-relational','order-convex']:
        task=json.loads((ROOT/'inputs'/f'{name}.json').read_text())
        cert=certificate(task)
        value=replay(task,cert)
        retained[name]={'task':task,'certificate':cert,'value':str(value)}
        reference=json.loads((ROOT/'results'/f'{name}.certificate.json').read_text())
        if cert != reference: raise RuntimeError(f'{name} producer changed')
    random_records=[]
    for seed in range(710,730):
        task=random_task(seed)
        cert=certificate(task)
        value=replay(task,cert)
        random_records.append({'seed':seed,'task':task,'certificate':cert,'value':str(value)})
    # Four independent corruption classes must be rejected.
    negative=0
    task=retained['order-relational']['task'];cert=retained['order-relational']['certificate']
    variants=[]
    bad=copy.deepcopy(cert);bad['value']='0';variants.append(bad)
    bad=copy.deepcopy(cert);bad['proofs'][0]['lambda'][0]='2';variants.append(bad)
    bad=copy.deepcopy(cert);bad['proofs'][0]['transport'][0][0][0]='1';variants.append(bad)
    bad=copy.deepcopy(cert);bad['proofs'][0]['dual_alpha']='9';variants.append(bad)
    for bad in variants:
        try: replay(task,bad)
        except (Invalid,ValueError): negative+=1
    if negative != len(variants): raise RuntimeError('corrupt certificate accepted')

    # The set-valued example cannot be separated by one fixed upward event,
    # yet the correlated target-law frame exposes positive loss.
    direct=direct_event_gap(task)
    contextual=F(cert['value'])
    if direct != 0 or contextual != F(1,4):
        raise RuntimeError('relational witness separation changed')

    pos=json.loads((ROOT/'inputs/join-tree.json').read_text())
    jc=join_tree.certificate(pos)
    generated_cells=join_tree.replay(pos,jc)

    # The retained evidence is a real replay input, not a file copied and then
    # compared with itself.  Re-establish it independently and require exact
    # equality with the deterministic canonical certificate generated above.
    retained_path=ROOT/'results/join-tree.certificate.json'
    retained_jc=join_tree.read_json(retained_path)
    retained_cells=join_tree.replay(pos,retained_jc)
    if retained_jc != jc:
        raise RuntimeError('retained join-tree certificate differs from canonical generation')

    # One-cell corruption in an isolated copy must fail replay.  The retained
    # input itself is never modified or deleted.
    mutation_rejected=False
    with tempfile.TemporaryDirectory(prefix='join-tree-single-cell-') as td:
        mutated=copy.deepcopy(retained_jc)
        first_cell=next(iter(mutated['law']))
        mutated['law'][first_cell]='1/4' if mutated['law'][first_cell] != '1/4' else '1/3'
        mutation_path=Path(td)/'mutated-join-tree.certificate.json'
        mutation_path.write_text(json.dumps(mutated,indent=2)+'\n',encoding='utf-8')
        try:
            join_tree.replay(pos,join_tree.read_json(mutation_path))
        except join_tree.Invalid:
            mutation_rejected=True
    if not mutation_rejected:
        raise RuntimeError('single-cell join-tree corruption was accepted')

    rejected=[]
    for filename in ['join-cycle-negative.json','join-separator-negative.json']:
        try: join_tree.certificate(json.loads((ROOT/'inputs'/filename).read_text()))
        except join_tree.Invalid: rejected.append(filename)
    if len(rejected)!=2: raise RuntimeError('invalid dependency input accepted')

    grid=oracle_grid()
    if grid['transport_upset_mismatches'] or grid['triangle_violations']:
        raise RuntimeError('finite order oracle mismatch')
    scientific={
      'retained_cases':{k:v['value'] for k,v in retained.items()},
      'random_exact_certificates':len(random_records),
      'random_seeds':[r['seed'] for r in random_records],
      'negative_certificates_rejected':negative,
      'relational_witness':{'direct_fixed_upset_gap':str(direct),
                            'correlated_frame_contextual_loss':str(contextual)},
      'point_oracle':grid,
      'dependency':{'join_tree_global_cells':generated_cells,
                    'generated_certificate_replayed':True,
                    'retained_certificate_replayed':True,
                    'retained_certificate_cells':retained_cells,
                    'retained_matches_generated':True,
                    'single_cell_mutation_rejected':True,
                    'mutation_used_isolated_copy':True,
                    'retained_input_preserved':True,
                    'negative_inputs_rejected':rejected},
      'scope':'finite exact validation; written proofs establish the general finite theorems'
    }
    (ROOT/'results/order-certificates.json').write_text(json.dumps(
        {'retained':retained,'random':random_records},indent=2)+'\n')
    (ROOT/'results/dependency.certificate.json').write_text(json.dumps(jc,indent=2)+'\n')
    (ROOT/'results/order-campaign.json').write_text(json.dumps(scientific,indent=2)+'\n')
    resources={'result':scientific,'wall_seconds':time.perf_counter()-start,
               'cpu_seconds':time.process_time()-cpu,
               'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               'one_worker':True}
    (ROOT/'results/order-resources.json').write_text(json.dumps(resources,indent=2)+'\n')
    print(json.dumps(scientific,sort_keys=True))

if __name__=='__main__':
    main()
