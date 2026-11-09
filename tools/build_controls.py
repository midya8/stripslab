"""Original synthetic planning controls, no benchmark source examples."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def action(pre=(),add=(),delete=()):return dict(pre=list(pre),add=list(add),delete=list(delete))
def control(name,m,initial,goal,actions):return dict(name=name,input=dict(facts=m,initial=initial,goal=goal,actions=actions))
def controls():
 return [
 control('One action, two goals: additive double counting',2,[],[0,1],[action(add=[0,1])]),
 control('Consumable resource: relaxed solvability hides a dead end',3,[0],[1,2],[action([0],[1],[0]),action([0],[2],[0])]),
 control('Restoring a consumed resource costs a real action',3,[0],[1,2],[action([0],[1],[0]),action([0],[2],[0]),action(add=[0])]),
 control('Two independent goals: max ignores combined effort',2,[],[0,1],[action(add=[0]),action(add=[1])]),
 control('All shortest action orders are retained',3,[],[0,1,2],[action(add=[0]),action(add=[1]),action(add=[2])]),
 control('Duplicate actions retain separate plan identities',2,[],[1],[action(add=[0]),action(add=[0]),action([0],[1])]),
 control('Initially satisfied goal: one empty shortest plan',2,[0],[0],[action([0],[1],[0])]),
 control('No facts, no actions, empty goal',0,[],[],[]),
 control('Cyclic prerequisites never start',2,[],[0],[action([1],[0]),action([0],[1])]),
 control('A reachable irreversible trap',3,[0],[2],[action([0],[1],[0]),action([0],[2])]),
 control('Self loops do not inflate shortest plan counts',2,[],[1],[action(),action(add=[0]),action([0],[0]),action([0],[1])]),
 control('Six facts with ordered prerequisites',6,[],[5],[action(add=[0])]+[action([i-1],[i]) for i in range(1,6)]),
 control('An impossible goal with no actions',1,[],[0],[]),
 control('Empty precondition deletes without adding',2,[0],[1],[action(delete=[0]),action([0],[1])]),
 ]
if __name__=='__main__':
 (ROOT/'docs/controls.json').write_text(json.dumps(controls(),indent=2)+'\n')
 (ROOT/'examples/task.json').write_text(json.dumps(controls()[1]['input'],indent=2)+'\n')
# Search control: three individually cheap goals distract h-add from a shared route.
shared=dict(facts=4,initial=[],goal=[0,1,2],actions=[dict(pre=[],add=[3],delete=[]),dict(pre=[3],add=[0,1,2],delete=[]),*[dict(pre=[],add=[i],delete=[]) for i in range(3)]])
search=[dict(name='h-add selects a three-step plan instead of the two-step optimum',input=shared)]+json.loads((ROOT/'docs/controls.json').read_text())
(ROOT/'docs/search-controls.json').write_text(json.dumps(search,indent=2)+'\n')

# Static action-availability controls retain original action identities.
shortcut=[action(add=[2]),action(add=[0]),action([0],[1]),action([1],[2])]
availability=[control('A representative action is not required: duplicate shortcut and longer detour',3,[],[2],shortcut+[action(add=[2])]),
 control('Required for optimality, not solvability: one shortcut and longer detour',3,[],[2],shortcut),
 control('Six facts and eight actions: duplicate shortcuts plus a six-step detour',6,[],[5],[action(add=[5]),action(add=[5]),action(add=[0])]+[action([i-1],[i]) for i in range(1,6)])]+search
(ROOT/'docs/sensitivity-controls.json').write_text(json.dumps(availability,indent=2)+'\n')
