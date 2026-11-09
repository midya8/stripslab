import json, random, unittest
from pathlib import Path
from stripslab import audit

ROOT=Path(__file__).resolve().parents[1]

def reference(x):
    """Independent set successors, Floyd-Warshall and bounded walk counting."""
    m=x['facts'];n=2**m;sets=[{f for f in range(m) if s//2**f%2} for s in range(n)]
    goals=[i for i,s in enumerate(sets) if set(x['goal'])<=s]
    initial=sum(2**f for f in x['initial'])
    matrices=[];graphs=[]
    for relaxed in [False,True]:
        d=[[0 if s==t else n+1 for t in range(n)] for s in range(n)];graph=[]
        for s,ss in enumerate(sets):
            row=[]
            for i,a in enumerate(x['actions']):
                if set(a['pre'])<=ss:
                    tt=(ss if relaxed else ss-set(a['delete']))|set(a['add']);t=sets.index(tt)
                    row.append((i,t));d[s][t]=min(d[s][t],1)
            graph.append(row)
        for k in range(n):
            for s in range(n):
                for t in range(n):d[s][t]=min(d[s][t],d[s][k]+d[k][t])
        matrices.append(d);graphs.append(graph)
    r=audit(x)
    for s,row in enumerate(r['states']):
        selfacts={w['action']:w for w in row['transitions']}
        for i,a in enumerate(x['actions']):
            w=selfacts[i];missing=sorted(set(a['pre'])-sets[s]);assert w['missing_preconditions']==missing
            if not missing:
                actual=(sets[s]-set(a['delete']))|set(a['add']);assert sets[w['successor']]==actual
                assert w['added']==sorted(actual-sets[s]);assert w['removed']==sorted(sets[s]-actual)
            else:assert w['successor'] is None and not w['applicable']
        assert row['distance_from_initial']==(matrices[0][initial][s] if matrices[0][initial][s]<=n else None)
        for mode,field in enumerate(['exact','relaxed']):
            d=min((matrices[mode][s][g] for g in goals),default=n+1);d=d if d<=n else None;f=row[field]
            assert f['distance']==d,(x,s,field)
            walks=[0]*n;walks[s]=1
            if d is not None:
                for _ in range(d):
                    nxt=[0]*n
                    for t,v in enumerate(walks):
                        for a,u in graphs[mode][t]:nxt[u]+=v
                    walks=nxt
                assert int(f['plan_count'])==sum(walks[g] for g in goals)
                t=s
                for a in f['representative']:
                    t=next(u for ai,u in graphs[mode][t] if ai==a)
                assert t in goals and len(f['representative'])==d
                expected=[] if d==0 else [[a,t] for a,t in graphs[mode][s] if min(matrices[mode][t][g] for g in goals)==d-1]
                assert f['choices']==expected
            else:assert f['plan_count']=='0' and f['representative'] is None and f['choices']==[]
        for mode in ['hmax','hadd']:
            # Enumerate derivation-tree height by memoized recursion, no graph propagation.
            from functools import lru_cache
            @lru_cache(None)
            def tree(f,height):
                if f in sets[s]:return 0
                if height==0:return None
                candidates=[]
                for a in x['actions']:
                    if f in a['add']:
                        vals=[tree(p,height-1) for p in a['pre']]
                        if None not in vals:candidates.append(1+(sum(vals) if mode=='hadd' else max(vals,default=0)))
                return min(candidates,default=None)
            costs=[tree(f,m) for f in range(m)];assert row[mode]['fact_costs']==costs
            vals=[costs[f] for f in x['goal']];value=None if None in vals else sum(vals) if mode=='hadd' else max(vals,default=0)
            assert row[mode]['value']==value
            rounds=row[mode]['rounds'];assert rounds[-1]==rounds[-2]==costs
            for before,after in zip(rounds,rounds[1:]):
                expected=before[:]
                for a in x['actions']:
                    vals=[before[f] for f in a['pre']]
                    if None not in vals:
                        c=1+(sum(vals) if mode=='hadd' else max(vals,default=0))
                        for f in a['add']:expected[f]=min(expected[f],c) if expected[f] is not None else c
                assert after==expected
            for f,ach in enumerate(row[mode]['best_achievers']):
                exp=[]
                if costs[f] not in [None,0]:
                    for i,a in enumerate(x['actions']):
                        vals=[costs[p] for p in a['pre']]
                        if f in a['add'] and None not in vals and 1+(sum(vals) if mode=='hadd' else max(vals,default=0))==costs[f]:exp.append(i)
                assert ach==exp
        hm,ha,hp,real=row['hmax']['value'],row['hadd']['value'],row['relaxed']['distance'],row['exact']['distance']
        assert (hm is None)==(ha is None)==(hp is None)
        if hp is not None:
            assert hm<=hp<=ha
            if real is not None:assert hp<=real
        elif real is not None:raise AssertionError('relaxation rejected a real plan')
    best=r['initial_exact']['distance'];expected=[]
    for s,row in enumerate(r['states']):
        for a,t in graphs[0][s]:
            tail=r['states'][t]['exact']['distance'];head=row['distance_from_initial']
            if best is not None and head is not None and tail is not None and head+1+tail==best:expected.append(dict(source=s,action=a,target=t))
    assert r['optimal_plan_edges']==expected
    assert r['initial_exact']==r['states'][initial]['exact']
    assert r['initial_relaxed']==r['states'][initial]['relaxed']
    assert r['goal_states']==goals
    assert r['reachable_states']==[s for s in range(n) if matrices[0][initial][s]<=n]
    assert r['reachable_dead_ends']==[row['mask'] for row in r['states'] if row['reachable'] and row['exact']['distance'] is None]
    assert r['reachable_hidden_dead_ends']==[row['mask'] for row in r['states'] if row['reachable'] and row['exact']['distance'] is None and row['relaxed']['distance'] is not None]
    assert r['reachable_hadd_overestimates']==[row['mask'] for row in r['states'] if row['reachable'] and row['exact']['distance'] is not None and row['hadd']['value'] is not None and row['hadd']['value']>row['exact']['distance']]
    for row in r['states']:
        assert row['goal']==(row['mask'] in goals)
        assert row['relaxation_hides_dead_end']==(row['exact']['distance'] is None and row['relaxed']['distance'] is not None)
        assert row['hadd_overestimates']==(row['exact']['distance'] is not None and row['hadd']['value'] is not None and row['hadd']['value']>row['exact']['distance'])
    return r

class Tests(unittest.TestCase):
    def test_controls(self):
        for c in json.loads((ROOT/'docs/controls.json').read_text()):reference(c['input'])
    def test_exhaustive_one_fact(self):
        from itertools import product
        actions=[dict(pre=[0] if p else [],add=[0] if a else [],delete=[0] if d else []) for p,a,d in product(range(2),repeat=3) if not (a and d)]
        for initial,goal,action in product(range(2),range(2),[None]+actions):reference(dict(facts=1,initial=[0] if initial else [],goal=[0] if goal else [],actions=[] if action is None else [action]))
    def test_seeded(self):
        rng=random.Random(4821)
        for _ in range(100):
            m=rng.randrange(4);subset=lambda:[f for f in range(m) if rng.randrange(2)]
            actions=[]
            for _ in range(rng.randrange(5)):
                pre,add,delete=subset(),subset(),subset();actions.append(dict(pre=pre,add=add,delete=[f for f in delete if f not in add]))
            reference(dict(facts=m,initial=subset(),goal=subset(),actions=actions))
    def test_strict_controls(self):
        reports=[audit(c['input']) for c in json.loads((ROOT/'docs/controls.json').read_text())]
        self.assertEqual((reports[0]['initial_exact']['distance'],reports[0]['states'][0]['hadd']['value']),(1,2))
        self.assertIsNone(reports[1]['initial_exact']['distance']);self.assertEqual(reports[1]['initial_relaxed']['distance'],2)
        self.assertEqual((reports[2]['initial_exact']['distance'],reports[2]['initial_relaxed']['distance']),(3,2))
        self.assertEqual(reports[4]['initial_exact']['plan_count'],'6');self.assertEqual(reports[5]['initial_exact']['plan_count'],'2')
        self.assertEqual(reports[6]['initial_exact']['representative'],[]);self.assertEqual(reports[7]['initial_exact']['plan_count'],'1')
    def test_validation(self):
        base=dict(facts=2,initial=[],goal=[],actions=[])
        bad=[{},dict(base,facts=True),dict(base,facts=2.0),dict(base,facts=7),dict(base,initial=[0,0]),dict(base,goal=[2]),dict(base,actions=[dict(pre=[],add=[0],delete=[0])]),dict(base,actions=[dict(pre=[],add=[],delete=[],cost=1)]),dict(base,actions=[dict(pre=[],add=[],delete=[])]*9),dict(base,initial=[False])]
        for x in bad:
            with self.assertRaises(ValueError):audit(x)
