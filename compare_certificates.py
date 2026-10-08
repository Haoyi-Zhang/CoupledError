"""Exact semantic comparison for nonunique LP proof witnesses."""
from fractions import Fraction
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent/'src'))
from order_verify import replay


def compare_order_record(a, b):
    if ({k:v for k,v in a.items() if k!='certificate'} !=
            {k:v for k,v in b.items() if k!='certificate'}):
        raise ValueError('certificate input, seed, or declared value changed')
    task=a['task']
    av=replay(task,a['certificate'])
    bv=replay(task,b['certificate'])
    if av!=bv or av!=Fraction(a['value']):
        raise ValueError('certificate objective changed')
    ap=[Fraction(p['value']) for p in a['certificate']['proofs']]
    bp=[Fraction(p['value']) for p in b['certificate']['proofs']]
    if ap!=bp:
        raise ValueError('per-generator optimum changed')


def compare_order_certificates(left,right):
    if set(left)!= {'retained','random'} or set(right)!=set(left):
        raise ValueError('certificate campaign shape')
    if set(left['retained'])!=set(right['retained']) or len(left['random'])!=len(right['random']):
        raise ValueError('certificate campaign coverage')
    pairs=[(left['retained'][k],right['retained'][k]) for k in sorted(left['retained'])]
    pairs+=list(zip(left['random'],right['random']))
    for a,b in pairs:
        compare_order_record(a,b)
    return len(pairs)
