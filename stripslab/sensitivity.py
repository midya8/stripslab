"""Exact static action-availability enumeration, not stochastic reliability."""
from collections import deque
from .core import audit


def audit_sensitivity(task):
    base = audit(task)
    states, start = base['states'], base['initial_mask']
    n, m = len(states), len(base['input']['actions'])
    full = (1 << m) - 1
    goals = [s['mask'] for s in states if s['goal']]
    scenarios = []
    for enabled in range(full + 1):
        adjacency = [[(t['action'], t['successor']) for t in s['transitions']
                      if t['applicable'] and enabled & (1 << t['action'])] for s in states]
        incoming = [[] for _ in states]
        for s, edges in enumerate(adjacency):
            for _, t in edges:
                incoming[t].append(s)
        distance, count = [None] * n, [0] * n
        distance[start], count[start] = 0, 1
        queue = deque([start])
        while queue:
            s = queue.popleft()
            for _, t in adjacency[s]:
                if distance[t] is None:
                    distance[t] = distance[s] + 1
                    queue.append(t)
                if distance[t] == distance[s] + 1:
                    count[t] += count[s]
        suffix = [None] * n
        queue = deque(goals)
        for s in goals:
            suffix[s] = 0
        while queue:
            t = queue.popleft()
            for s in incoming[t]:
                if suffix[s] is None:
                    suffix[s] = suffix[t] + 1
                    queue.append(s)
        optimum = suffix[start]
        edges = []
        if optimum is not None:
            for s in range(n):
                for a, t in adjacency[s]:
                    if distance[s] is not None and suffix[t] is not None and distance[s] + 1 + suffix[t] == optimum:
                        edges.append(dict(source=s, action=a, target=t))
        plan = None
        if optimum is not None:
            plan, s = [], start
            for _ in range(optimum):
                a, t = next((a, t) for a, t in adjacency[s] if suffix[t] is not None and suffix[t] + 1 == suffix[s])
                plan.append(a)
                s = t
        scenarios.append(dict(enabled_mask=enabled, enabled_actions=[a for a in range(m) if enabled & (1 << a)],
                              removed_actions=[a for a in range(m) if not enabled & (1 << a)],
                              distance=optimum, plan_count=str(sum(count[g] for g in goals if distance[g] == optimum)) if optimum is not None else '0',
                              representative=plan, distances_from_initial=distance, distances_to_goal=suffix,
                              shortest_prefix_counts=[str(c) for c in count], optimal_edges=edges))
    baseline = scenarios[full]
    solved = baseline['distance'] is not None
    def minima(predicate):
        return [mask for mask in range(full + 1) if predicate(mask) and
                all(not predicate(mask ^ (1 << a)) for a in range(m) if mask & (1 << a))]
    sufficient = minima(lambda mask: scenarios[mask]['distance'] is not None)
    optimal = minima(lambda mask: scenarios[mask]['distance'] == baseline['distance']) if solved else None
    cuts = minima(lambda removed: scenarios[full ^ removed]['distance'] is None) if solved else None
    optimal_cuts = minima(lambda removed: scenarios[full ^ removed]['distance'] != baseline['distance']) if solved else None
    single = []
    for a in range(m):
        s = scenarios[full ^ (1 << a)]
        single.append(dict(action=a, enabled_mask=s['enabled_mask'], used_by_representative=None if not solved else a in baseline['representative'],
                           necessary_for_optimality=None if not solved else s['distance'] != baseline['distance'],
                           necessary_for_solvability=None if not solved else s['distance'] is None))
    return dict(schema='stripslab-sensitivity-v1', input=base['input'], base=base, baseline_enabled_mask=full,
                scenarios=scenarios, minimal_sufficient_enabled=sufficient, minimal_optimal_enabled=optimal,
                minimal_solvability_cuts=cuts, minimal_optimality_cuts=optimal_cuts, single_removals=single,
                baseline_solvable=solved)
