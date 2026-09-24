"""Independent exact certificate replay; imports no search/optimizer module.

This is a small executable checker, not a mechanized general soundness proof.
Limits bound untrusted local files. They are implementation limits, not a
claim about the complexity of arbitrary polytope containment.
"""
import json
import sys
from fractions import Fraction
from pathlib import Path
from math import lcm

class Invalid(ValueError):
    pass

def require(test, message):
    if not test:
        raise Invalid(message)

def rat(x):
    require(type(x) is str and len(x)<=160, 'rational must be a short string')
    require(all(c in '-0123456789/' for c in x),'only integer or fraction notation allowed')
    try:
        value=Fraction(x)
    except (ValueError,ZeroDivisionError) as e:
        raise Invalid('invalid rational') from e
    require(value.numerator.bit_length()<=256 and value.denominator.bit_length()<=256,
            'rational bit limit exceeded')
    return value

def vector(x,n):
    require(type(x) is list and len(x)==n,'vector length mismatch')
    return tuple(rat(v) for v in x)

def contract(x):
    require(type(x) is dict and set(x)=={'states','vertices'},'invalid contract keys')
    k=x['states']
    require(type(k) is int and 1<=k<=4,'invalid state count')
    vs=x['vertices'];require(type(vs) is list and 1<=len(vs)<=5,'invalid generator count')
    out=[]
    for v in vs:
        require(type(v) is dict and set(v)=={'p','a'},'invalid vertex keys')
        p=vector(v['p'],k);a=vector(v['a'],k)
        require(sum(p)==1 and all(0<=t<=s for t,s in zip(a,p)),'invalid probability mass')
        out.append((p,a))
    return tuple(out)

def inner(x,y):
    require(len(x)==len(y),'inner product dimension mismatch')
    return sum((a*b for a,b in zip(x,y)),Fraction(0))

def prior(lam,source,target):
    weights=vector(lam,len(source))
    require(all(x>=0 for x in weights) and sum(weights)==1,'invalid convex weights')
    for s,expect in enumerate(target):
        require(sum(w*v[0][s] for w,v in zip(weights,source))==expect,'boundary mismatch')
    return weights

def replay(task,cert):
    require(type(task) is dict and set(task)=={'old','new'},'invalid task keys')
    old,new=contract(task['old']),contract(task['new'])
    denominator=lcm(*(v.denominator for p,a in old+new for v in p+a))
    require(denominator<=65536,'input common denominator exceeds 65536')
    k=len(old[0][0]);require(len(new[0][0])==k,'state count mismatch')
    keys={'kind','value','old_to_new_prior','new_to_old_prior','proofs','worst_vertex','context_success'}
    require(type(cert) is dict and set(cert)==keys,'invalid certificate keys')
    require(cert['kind']=='contextual-loss','wrong certificate kind')
    for field,source,targets in [('old_to_new_prior',new,old),('new_to_old_prior',old,new)]:
        weights=cert[field]
        require(type(weights) is list and len(weights)==len(targets),'missing domain proof')
        for w,(p,a) in zip(weights,targets):
            prior(w,source,p)
    proofs=cert['proofs'];require(type(proofs) is list and len(proofs)==len(new),'missing vertex proof')
    losses=[]
    for pr,(p,a) in zip(proofs,new):
        pk={'value','lambda','slack','y','w','primal_systems','dual_systems'}
        require(type(pr) is dict and set(pr)==pk,'invalid vertex proof keys')
        for count in ['primal_systems','dual_systems']:
            require(type(pr[count]) is int and 0<=pr[count]<=100000,'invalid search metadata')
        lam=prior(pr['lambda'],old,p)
        t=vector(pr['slack'],k); y=vector(pr['y'],k+1); w=vector(pr['w'],k)
        require(all(z>=0 for z in t),'negative primal slack')
        for s in range(k):
            require(t[s]>=sum(l*v[1][s] for l,v in zip(lam,old))-a[s],'primal inequality violated')
        require(all(0<=z<=1 for z in w),'dual box violated')
        for po,ao in old:
            require(y[0]+inner(po,y[1:])<=inner(ao,w),'dual vertex inequality violated')
        claim=rat(pr['value'])
        require(claim==sum(t)==y[0]+inner(p,y[1:])-inner(a,w),'primal-dual objective mismatch')
        require(0<=claim<=1,'loss outside [0,1]')
        losses.append(claim)
    value=rat(cert['value'])
    require(value==max(losses),'maximum does not match vertex losses')
    idx=cert['worst_vertex']
    require(type(idx) is int and 0<=idx<len(new) and losses[idx]==value,'invalid maximizing vertex')
    p,a=new[idx]
    b=vector(cert['context_success'],k)
    require(all(z==q-t for z,q,t in zip(b,p,a)),'countercontext mismatch')
    return value

def read_json(path):
    p=Path(path)
    require(p.is_file() and p.stat().st_size<=2**20,'file missing or exceeds one MiB')
    def pairs(items):
        d={}
        for k,v in items:
            require(k not in d,'duplicate JSON key')
            d[k]=v
        return d
    try:
        return json.loads(p.read_text(encoding='utf-8'),object_pairs_hook=pairs)
    except (UnicodeError,ValueError,RecursionError) as e:
        raise Invalid('invalid JSON') from e

def main():
    if len(sys.argv)!=3:
        print('usage: python src/verify.py TASK.json CERTIFICATE.json',file=sys.stderr)
        return 2
    try:
        value=replay(read_json(sys.argv[1]),read_json(sys.argv[2]))
    except (Invalid,OSError,TypeError,KeyError,IndexError) as e:
        print(f'REJECT: {e}',file=sys.stderr); return 1
    print(f'ACCEPT: exact worst contextual reliability loss = {value}')
    return 0

if __name__=='__main__':
    raise SystemExit(main())
