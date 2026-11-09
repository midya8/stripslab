"""Original bounded state-graph and delete-relaxation implementation."""
from collections import deque


def validate(x):
    if not isinstance(x, dict) or set(x) != {'facts', 'initial', 'goal', 'actions'}:
        raise ValueError('Expected exactly facts, initial, goal, actions')
    m = x['facts']
    if type(m) is not int or not 0 <= m <= 6:
        raise ValueError('facts must be an integer in 0..6')
    def subset(v):
        if not isinstance(v, list) or any(type(i) is not int or not 0 <= i < m for i in v) or len(set(v)) != len(v):
            raise ValueError('Fact lists must contain distinct valid integer indices')
        return sorted(v)
    initial, goal = subset(x['initial']), subset(x['goal'])
    if not isinstance(x['actions'], list) or len(x['actions']) > 8:
        raise ValueError('At most eight actions')
    actions = []
    for a in x['actions']:
        if not isinstance(a, dict) or set(a) != {'pre', 'add', 'delete'}:
            raise ValueError('Each action has exactly pre, add, delete')
        a = {k: subset(a[k]) for k in ['pre', 'add', 'delete']}
        if set(a['add']) & set(a['delete']):
            raise ValueError('add and delete must be disjoint')
        actions.append(a)
    return dict(facts=m, initial=initial, goal=goal, actions=actions)


def _mask(xs):
    return sum(1 << i for i in xs)


def _bits(mask, m):
    return [i for i in range(m) if mask & (1 << i)]


def _bfs(edges, seeds):
    d = [None] * len(edges)
    q = deque()
    for s in seeds:
        d[s] = 0
        q.append(s)
    while q:
        s = q.popleft()
        for t in edges[s]:
            if d[t] is None:
                d[t] = d[s] + 1
                q.append(t)
    return d


def _family(graph, goals):
    reverse = [[] for _ in graph]
    for s, row in enumerate(graph):
        for a, t in row:
            reverse[t].append(s)
    distance = _bfs(reverse, goals)
    choices = [[] for _ in graph]
    counts = [0] * len(graph)
    plans = [None] * len(graph)
    for s in sorted((s for s, d in enumerate(distance) if d is not None), key=lambda s: (distance[s], s)):
        if distance[s] == 0:
            counts[s], plans[s] = 1, []
        else:
            choices[s] = [[a, t] for a, t in graph[s] if distance[t] is not None and distance[t] + 1 == distance[s]]
            counts[s] = sum(counts[t] for a, t in choices[s])
            a, t = choices[s][0]
            plans[s] = [a] + plans[t]
    return [dict(distance=distance[s], choices=choices[s], plan_count=str(counts[s]), representative=plans[s]) for s in range(len(graph))]


def _heuristic(state, actions, goal, m, mode):
    cost = [0 if state & (1 << f) else None for f in range(m)]
    rounds = [cost[:]]
    def aggregate(xs):
        if any(v is None for v in xs):
            return None
        return sum(xs) if mode == 'add' else max(xs, default=0)
    while True:
        nxt = cost[:]
        for a in actions:
            c = aggregate([cost[f] for f in a['pre']])
            if c is not None:
                for f in a['add']:
                    if nxt[f] is None or c + 1 < nxt[f]:
                        nxt[f] = c + 1
        rounds.append(nxt[:])
        if nxt == cost:
            break
        cost = nxt
    achievers = []
    for f in range(m):
        best = []
        if cost[f] is not None and cost[f] != 0:
            for i, a in enumerate(actions):
                c = aggregate([cost[p] for p in a['pre']])
                if f in a['add'] and c is not None and c + 1 == cost[f]:
                    best.append(i)
        achievers.append(best)
    return dict(value=aggregate([cost[f] for f in goal]), fact_costs=cost, rounds=rounds, best_achievers=achievers)


def audit(raw):
    x = validate(raw)
    m, actions = x['facts'], x['actions']
    initial, goal = _mask(x['initial']), _mask(x['goal'])
    encoded = [tuple(_mask(a[k]) for k in ['pre', 'add', 'delete']) for a in actions]
    graph, relaxed, transitions = [], [], []
    for s in range(1 << m):
        row, rr, witnesses = [], [], []
        for i, (pre, add, delete) in enumerate(encoded):
            missing = pre & ~s
            t = (s & ~delete) | add if not missing else None
            rt = s | add if not missing else None
            if t is not None:
                row.append([i, t]); rr.append([i, rt])
            witnesses.append(dict(action=i, missing_preconditions=_bits(missing, m), applicable=not bool(missing), successor=t, relaxed_successor=rt, added=_bits(t & ~s, m) if t is not None else [], removed=_bits(s & ~t, m) if t is not None else []))
        graph.append(row); relaxed.append(rr); transitions.append(witnesses)
    goals = [s for s in range(1 << m) if s & goal == goal]
    real_family, relaxed_family = _family(graph, goals), _family(relaxed, goals)
    from_initial = _bfs([[t for a, t in row] for row in graph], [initial])
    states = []
    for s in range(1 << m):
        real, relax = real_family[s], relaxed_family[s]
        hmax = _heuristic(s, actions, x['goal'], m, 'max')
        hadd = _heuristic(s, actions, x['goal'], m, 'add')
        states.append(dict(mask=s, facts=_bits(s, m), reachable=from_initial[s] is not None, distance_from_initial=from_initial[s], goal=s in goals, transitions=transitions[s], exact=real, relaxed=relax, hmax=hmax, hadd=hadd, relaxation_hides_dead_end=real['distance'] is None and relax['distance'] is not None, hadd_overestimates=real['distance'] is not None and hadd['value'] is not None and hadd['value'] > real['distance']))
    optimal = real_family[initial]['distance']
    optimal_edges = []
    if optimal is not None:
        for s, row in enumerate(graph):
            for a, t in row:
                if from_initial[s] is not None and real_family[t]['distance'] is not None and from_initial[s] + 1 + real_family[t]['distance'] == optimal:
                    optimal_edges.append(dict(source=s, action=a, target=t))
    return dict(schema='stripslab.audit.v1', input=x, initial_mask=initial, goal_mask=goal, states=states, reachable_states=[s['mask'] for s in states if s['reachable']], goal_states=goals, initial_exact=real_family[initial], initial_relaxed=relaxed_family[initial], optimal_plan_edges=optimal_edges, reachable_dead_ends=[s['mask'] for s in states if s['reachable'] and s['exact']['distance'] is None], reachable_hidden_dead_ends=[s['mask'] for s in states if s['reachable'] and s['relaxation_hides_dead_end']], reachable_hadd_overestimates=[s['mask'] for s in states if s['reachable'] and s['hadd_overestimates']])
