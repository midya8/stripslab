"""Deterministic search witnesses over the existing finite planning audit."""
import heapq
from .core import audit

MODES = ('zero', 'hmax', 'hadd', 'hplus')


def _run(base, values):
    states, start = base['states'], base['initial_mask']
    n = len(states)
    best = [None] * n
    paths = [None] * n
    expanded = [0] * n
    opened = set()
    heap, steps = [], []
    generated, reopened = 1, 0
    def entry(s):
        h = values[s]
        return dict(state=s, g=best[s], h=h, f=None if h is None else best[s] + h)
    def key(e):
        return (float('inf') if e['f'] is None else e['f'], e['g'], e['state'])
    def push(s):
        opened.add(s)
        heapq.heappush(heap, key(entry(s)))
    best[start], paths[start] = 0, []
    push(start)
    plan, cost, goal = None, None, None
    while opened:
        frontier = sorted((entry(s) for s in opened), key=key)
        # Obsolete heap labels are an implementation detail, not search steps.
        while True:
            f, g, s = heapq.heappop(heap)
            if s in opened and g == best[s]:
                break
        assert entry(s) == frontier[0]
        opened.remove(s)
        step = dict(index=len(steps), frontier=frontier, selected=entry(s), goal=states[s]['goal'], actions=[])
        steps.append(step)
        if states[s]['goal']:
            plan, cost, goal = paths[s][:], g, s
            break
        expanded[s] += 1
        for t in states[s]['transitions']:
            if not t['applicable']:
                continue
            target, candidate = t['successor'], g + 1
            previous = best[target]
            improved = previous is None or candidate < previous
            was_closed = expanded[target] > 0 and target not in opened
            did_reopen = improved and was_closed
            step['actions'].append(dict(action=t['action'], target=target, candidate_g=candidate,
                                        previous_g=previous, improved=improved, reopened=did_reopen))
            if improved:
                best[target] = candidate
                paths[target] = paths[s] + [t['action']]
                push(target)
                generated += 1
                reopened += int(did_reopen)
    optimum = base['initial_exact']['distance']
    admissibility = [s for s in range(n) if states[s]['exact']['distance'] is not None and
                     (values[s] is None or values[s] > states[s]['exact']['distance'])]
    consistency = []
    for s in range(n):
        for t in states[s]['transitions']:
            if t['applicable']:
                v = values[t['successor']]
                if v is not None and (values[s] is None or values[s] > 1 + v):
                    consistency.append([s, t['action'], t['successor']])
    return dict(values=values, steps=steps, final_frontier=sorted((entry(s) for s in opened), key=key),
                best_g=best, expansion_counts=expanded, expansions=sum(expanded), generated=generated,
                reopened=reopened, goal_state=goal, plan=plan, cost=cost,
                termination='goal_popped' if goal is not None else 'frontier_empty',
                exact_optimum=optimum, agrees_with_optimum=cost == optimum,
                regret=None if cost is None or optimum is None else cost - optimum,
                admissibility_violations=admissibility, consistency_violations=consistency)


def audit_search(task):
    base = audit(task)
    states = base['states']
    values = dict(zero=[0] * len(states), hmax=[s['hmax']['value'] for s in states],
                  hadd=[s['hadd']['value'] for s in states], hplus=[s['relaxed']['distance'] for s in states])
    return dict(schema='stripslab-search-v1', input=base['input'], base=base,
                tie_order=['f_ascending_infinity_last', 'g_ascending', 'state_mask_ascending'],
                runs={mode: _run(base, values[mode]) for mode in MODES})
