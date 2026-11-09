import json, random, unittest
from pathlib import Path
from stripslab.search import audit_search, _run
from stripslab import audit

ROOT=Path(__file__).resolve().parents[1]


def replay(base, run):
    """Replay each certificate against direct set transitions and independent labels."""
    x=base['input'];n=2**x['facts'];initial=sum(2**i for i in x['initial'])
    facts=[{i for i in range(x['facts']) if s//2**i%2} for s in range(n)]
    best={initial:0};paths={initial:[]};opened={initial};counts=[0]*n
    generated,reopened=1,0;goal=None;plan=None;cost=None
    h=run['values']
    def row(s):return dict(state=s,g=best[s],h=h[s],f=None if h[s] is None else best[s]+h[s])
    def order(s):return (best[s]+h[s] if h[s] is not None else float('inf'),best[s],s)
    for i,step in enumerate(run['steps']):
        assert step['index']==i
        assert step['frontier']==[row(s) for s in sorted(opened,key=order)]
        s=min(opened,key=order);assert step['selected']==row(s);opened.remove(s)
        isgoal=set(x['goal'])<=facts[s];assert step['goal']==isgoal
        if isgoal:
            assert i==len(run['steps'])-1 and step['actions']==[]
            goal,plan,cost=s,paths[s],best[s];break
        counts[s]+=1;events=[]
        for a,action in enumerate(x['actions']):
            if not set(action['pre'])<=facts[s]:continue
            target=facts.index((facts[s]-set(action['delete']))|set(action['add']))
            candidate=best[s]+1;previous=best.get(target)
            improved=previous is None or candidate<previous
            again=improved and counts[target]>0 and target not in opened
            events.append(dict(action=a,target=target,candidate_g=candidate,previous_g=previous,improved=improved,reopened=again))
            if improved:
                best[target]=candidate;paths[target]=paths[s]+[a];opened.add(target);generated+=1;reopened+=int(again)
        assert step['actions']==events
    assert run['goal_state']==goal and run['plan']==plan and run['cost']==cost
    assert run['termination']==('goal_popped' if goal is not None else 'frontier_empty')
    if goal is None:assert not opened
    assert run['final_frontier']==[row(s) for s in sorted(opened,key=order)]
    assert run['best_g']==[best.get(s) for s in range(n)]
    assert run['expansion_counts']==counts and run['expansions']==sum(counts)
    assert run['generated']==generated and run['reopened']==reopened
    optimum=base['initial_exact']['distance']
    assert run['exact_optimum']==optimum and run['agrees_with_optimum']==(cost==optimum)
    assert run['regret']==(None if cost is None or optimum is None else cost-optimum)
    admissibility=[];consistency=[]
    for s in range(n):
        d=base['states'][s]['exact']['distance']
        if d is not None and (h[s] is None or h[s]>d):admissibility.append(s)
        for a,action in enumerate(x['actions']):
            if set(action['pre'])<=facts[s]:
                t=facts.index((facts[s]-set(action['delete']))|set(action['add']))
                if h[t] is not None and (h[s] is None or h[s]>1+h[t]):consistency.append([s,a,t])
    assert run['admissibility_violations']==admissibility and run['consistency_violations']==consistency
    if plan is not None:
        s=set(x['initial'])
        for a in plan:
            act=x['actions'][a];assert set(act['pre'])<=s;s=(s-set(act['delete']))|set(act['add'])
        assert set(x['goal'])<=s and len(plan)==cost


class SearchTests(unittest.TestCase):
    def check(self,x):
        r=audit_search(x);assert r['base']==audit(x)
        assert r['tie_order']==['f_ascending_infinity_last','g_ascending','state_mask_ascending']
        for mode,run in r['runs'].items():
            replay(r['base'],run)
            expected=[0 if mode=='zero' else s['relaxed']['distance'] if mode=='hplus' else s[mode]['value'] for s in r['base']['states']]
            assert run['values']==expected
            if mode!='hadd':assert run['agrees_with_optimum'] and not run['admissibility_violations'] and not run['consistency_violations'] and run['reopened']==0
        return r
    def test_retained_controls_and_strict_suboptimality(self):
        for c in json.loads((ROOT/'docs/search-controls.json').read_text()):self.check(c['input'])
        c=json.loads((ROOT/'docs/search-controls.json').read_text())[0]
        r=self.check(c['input']);self.assertEqual(r['runs']['hadd']['cost'],3);self.assertEqual(r['runs']['hplus']['cost'],2)
        self.assertEqual(r['runs']['hadd']['regret'],1);self.assertFalse(r['runs']['hadd']['agrees_with_optimum'])
    def test_seeded_traces(self):
        rng=random.Random(23107)
        for _ in range(120):
            m=rng.randrange(5);subset=lambda:[f for f in range(m) if rng.randrange(2)]
            actions=[]
            for _ in range(rng.randrange(9)):
                add=subset();actions.append(dict(pre=subset(),add=add,delete=[f for f in subset() if f not in add]))
            self.check(dict(facts=m,initial=subset(),goal=subset(),actions=actions))
    def test_reopen_admissible_inconsistent_diagnostic(self):
        c=json.loads((ROOT/'examples/search-reopen.json').read_text());b=audit(c['input']);r=_run(b,c['values']);replay(b,r)
        self.assertGreater(r['reopened'],0);self.assertFalse(r['admissibility_violations']);self.assertTrue(r['consistency_violations']);self.assertTrue(r['agrees_with_optimum'])
    def test_validation_and_no_mutation(self):
        x=json.loads((ROOT/'docs/search-controls.json').read_text())[0]['input'];saved=json.dumps(x);self.check(x);self.assertEqual(json.dumps(x),saved)
        for bad in [{},dict(x,facts=True),dict(x,extra=0),dict(x,actions=[dict(pre=[],add=[0],delete=[0])])]:
            with self.assertRaises(ValueError):audit_search(bad)

if __name__=='__main__':unittest.main()
