"""Finite Boolean scope checks and exact projection of supplied joint-law lists.

The supplied lists denote convex hulls of complete local laws. This module
never claims to enumerate all models of an arbitrary constraint formula.
No code is evaluated from the input: expressions use the small grammar below.
"""
from fractions import Fraction as F
from itertools import product
from math import lcm
import re
from verify import Invalid, require, rat

NAME = re.compile(r'^[A-Za-z][A-Za-z0-9-]{0,31}$')


def names(xs, limit=12):
    require(type(xs) is list and len(xs)<=limit, 'invalid name list')
    require(all(type(x) is str and NAME.fullmatch(x) for x in xs), 'invalid variable name')
    require(len(set(xs))==len(xs), 'duplicate variable')
    return set(xs)


def expression(expr):
    """Validate shape, then return the syntactic variable support."""
    count = [0]
    def visit(e,depth):
        count[0] += 1
        require(count[0]<=256 and depth<=24, 'expression size limit')
        if type(e) is bool:
            return set()
        if type(e) is str:
            require(NAME.fullmatch(e) is not None, 'invalid expression variable')
            return {e}
        require(type(e) is list and 2<=len(e)<=9, 'invalid expression node')
        op=e[0]
        require(type(op) is str and op in ('not','and','or','if'), 'unknown Boolean operator')
        require((op=='not' and len(e)==2) or (op=='if' and len(e)==4) or
                (op in ('and','or') and len(e)>=3), 'Boolean operator arity')
        out=set()
        for child in e[1:]: out.update(visit(child,depth+1))
        return out
    return visit(expr,0)


def evaluate(expr, env):
    if type(expr) is bool: return expr
    if type(expr) is str: return bool(env[expr])
    op=expr[0]
    if op=='not': return not evaluate(expr[1],env)
    if op=='and': return all(evaluate(e,env) for e in expr[1:])
    if op=='or': return any(evaluate(e,env) for e in expr[1:])
    if op=='if': return evaluate(expr[2] if evaluate(expr[1],env) else expr[3],env)
    raise Invalid('expression was not validated')


def check_interface(obj):
    keys={'boundary','private','frame','success','constraints','monitor'}
    require(type(obj) is dict and set(obj)==keys, 'invalid interface keys')
    B=names(obj['boundary'],2);L=names(obj['private'],5);R=names(obj['frame'],8)
    g=obj['success']; require(type(g) is str and NAME.fullmatch(g), 'invalid success name')
    require(not (B&L or B&R or L&R) and g not in B|L|R,'interface variable collision')
    require(len(B|L|R|{g})<=12,'too many finite Boolean inputs')
    local=B|L|{g}; frame=B|R
    constraints=obj['constraints']
    require(type(constraints) is list and len(constraints)<=32,'constraint count limit')
    scopes=[]
    for c in constraints:
        require(type(c) is dict and set(c)=={'event','lower','upper'}, 'invalid constraint')
        support=expression(c['event'])
        require(support<=local or support<=frame,'crossing law constraint')
        lo,hi=rat(c['lower']),rat(c['upper'])
        require(0<=lo<=hi<=1,'invalid expectation interval')
        scopes.append(sorted(support))
    support=expression(obj['monitor'])
    require(support<=frame|{g},'monitor reads a private or undeclared variable')
    ambient=sorted(support-{g})
    checks=0
    for bits in product((False,True),repeat=len(ambient)):
        env=dict(zip(ambient,bits));env[g]=False
        lo=evaluate(obj['monitor'],env);env[g]=True
        hi=evaluate(obj['monitor'],env); checks+=1
        require(not lo or hi,'monitor is not monotone in the success event')
    return {'boundary_states':2**len(B),'law_scopes':scopes,
            'monotonicity_assignments':checks,
            'scope_condition':'closed finite scopes; no independence inferred'}


def validate_laws(obj, required_variables, constraints):
    require(type(obj) is dict and set(obj)=={'variables','laws'},'invalid joint-law object')
    vs=obj['variables']; have=names(vs,8)
    require(have==set(required_variables),'joint-law variables differ from declared scope')
    laws=obj['laws']
    require(type(laws) is list and 1<=len(laws)<=5,'joint-law generator count limit')
    relevant=[]
    for c in constraints:
        if expression(c['event'])<=have: relevant.append(c)
    parsed=[];denominator=1
    for cells in laws:
        require(type(cells) is list and 1<=len(cells)<=256,'joint-law cell count limit')
        law=[];seen=set()
        for cell in cells:
            require(type(cell) is dict and set(cell)=={'assignment','mass'},'invalid joint-law cell')
            bits=cell['assignment']
            require(type(bits) is list and len(bits)==len(vs) and
                    all(type(x) is int and x in (0,1) for x in bits),'invalid Boolean assignment')
            key=tuple(bits); require(key not in seen,'duplicate joint-law assignment');seen.add(key)
            mass=rat(cell['mass']);require(0<=mass<=1,'invalid cell mass')
            denominator=lcm(denominator,mass.denominator)
            require(denominator<=65536,'joint-law common denominator limit')
            law.append((dict(zip(vs,bits)),mass))
        require(sum(m for e,m in law)==1,'joint law is not normalized')
        for c in relevant:
            val=sum((m for e,m in law if evaluate(c['event'],e)),F(0))
            require(rat(c['lower'])<=val<=rat(c['upper']),'joint-law generator violates a constraint')
        parsed.append(law)
    return parsed


def project(laws,boundary,success):
    k=2**len(boundary);vertices=[]
    for law in laws:
        p=[F(0)]*k;a=[F(0)]*k
        for env,mass in law:
            index=0
            for name in boundary:index=2*index+env[name]
            p[index]+=mass
            if env[success]:a[index]+=mass
        vertices.append({'p':[str(x) for x in p],'a':[str(x) for x in a]})
    return {'states':k,'vertices':vertices}


def derive(model):
    require(type(model) is dict and set(model)=={'interface','old','new','frame'},'invalid source model')
    interface=model['interface'];report=check_interface(interface)
    B=interface['boundary'];L=interface['private'];R=interface['frame'];g=interface['success']
    constraints=interface['constraints']
    old=validate_laws(model['old'],B+L+[g],constraints)
    new=validate_laws(model['new'],B+L+[g],constraints)
    frame=validate_laws(model['frame'],B+R,constraints)
    task={'old':project(old,B,g),'new':project(new,B,g)}
    # A supplied frame is a real input, not a merely illustrative annotation.
    # Require each of its prior generators to be allowed by both components.
    # Convexity then covers every mixture of the frame generators. This is a
    # conservative source-route rule; the abstract loss supports domain
    # restriction more generally. Search remains outside independent replay.
    from exact import load_contract, prior_witness
    parsed_old,parsed_new=load_contract(task['old']),load_contract(task['new'])
    witnesses=[]
    for law in frame:
        prior=[F(0)]*(2**len(B))
        for env,mass in law:
            index=0
            for name in B:index=2*index+env[name]
            prior[index]+=mass
        old_w=prior_witness(parsed_old,prior)
        new_w=prior_witness(parsed_new,prior)
        require(old_w is not None and new_w is not None,
                'frame prior is outside a component prior domain')
        witnesses.append({'p':[str(x) for x in prior],
                          'old':[str(x) for x in old_w],
                          'new':[str(x) for x in new_w]})
    report['frame_prior_witnesses']=witnesses
    report['old_joint_laws']=len(old);report['new_joint_laws']=len(new)
    report['frame_joint_laws']=len(frame)
    report['projection']='exact image of supplied convex generators, not arbitrary constraint solving'
    return task,report
