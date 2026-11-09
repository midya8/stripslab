import copy
import json
import random
import unittest
from pathlib import Path
from stripslab.sensitivity import audit_sensitivity

ROOT = Path(__file__).resolve().parents[1]


def oracle(task, enabled):
    n = 1 << task['facts']
    start = sum(1 << f for f in task['initial'])
    goal = set(task['goal'])
    sets = [set(f for f in range(task['facts']) if s & (1 << f)) for s in range(n)]
    edges = []
    for s, facts in enumerate(sets):
        for a, action in enumerate(task['actions']):
            if enabled & (1 << a) and set(action['pre']) <= facts:
                target = (facts - set(action['delete'])) | set(action['add'])
                edges.append((s, a, sum(1 << f for f in target)))
    # Layer-by-layer walk counting, with no production transition records or queue.
    distance, counts, paths = [None] * n, [0] * n, [None] * n
    distance[start], counts[start], paths[start] = 0, 1, ()
    for depth in range(n):
        for s, a, t in edges:
            if distance[s] == depth and (distance[t] is None or distance[t] == depth + 1):
                distance[t] = depth + 1
                counts[t] += counts[s]
                candidate = paths[s] + (a,)
                if paths[t] is None or candidate < paths[t]:
                    paths[t] = candidate
    goals = [s for s in range(n) if goal <= sets[s]]
    ds = [distance[g] for g in goals if distance[g] is not None]
    best = min(ds) if ds else None
    suffix = [None] * n
    reached = set(goals)
    for g in goals:
        suffix[g] = 0
    for depth in range(n):
        parents = {s for s, _, t in edges if suffix[t] == depth} - reached
        for s in parents:
            suffix[s] = depth + 1
        reached |= parents
    optimum = [] if best is None else [dict(source=s, action=a, target=t) for s, a, t in edges
                 if distance[s] is not None and suffix[t] is not None and distance[s] + 1 + suffix[t] == best]
    return dict(distance=best, plan_count=str(sum(counts[g] for g in goals if distance[g] == best)) if best is not None else '0',
                representative=list(min(paths[g] for g in goals if distance[g] == best)) if best is not None else None,
                distances_from_initial=distance, distances_to_goal=suffix, shortest_prefix_counts=list(map(str, counts)), optimal_edges=optimum)


class SensitivityTests(unittest.TestCase):
    def check(self, task):
        before = copy.deepcopy(task)
        r = audit_sensitivity(task)
        self.assertEqual(task, before)
        m = len(task['actions'])
        full = (1 << m) - 1
        self.assertEqual(len(r['scenarios']), full + 1)
        for mask, s in enumerate(r['scenarios']):
            for k, v in oracle(r['input'], mask).items():
                self.assertEqual(s[k], v, (mask, k))
            self.assertEqual(s['enabled_mask'], mask)
            self.assertEqual(s['enabled_actions'], [a for a in range(m) if mask & (1 << a)])
            self.assertEqual(s['removed_actions'], [a for a in range(m) if not mask & (1 << a)])
        table = r['scenarios']
        solved = r['baseline_solvable']
        self.assertEqual(solved, table[full]['distance'] is not None)
        predicates = dict(minimal_sufficient_enabled=lambda mask: table[mask]['distance'] is not None)
        if solved:
            predicates.update(minimal_optimal_enabled=lambda mask: table[mask]['distance'] == table[full]['distance'],
                              minimal_solvability_cuts=lambda mask: table[full ^ mask]['distance'] is None,
                              minimal_optimality_cuts=lambda mask: table[full ^ mask]['distance'] != table[full]['distance'])
        else:
            for k in ['minimal_optimal_enabled', 'minimal_solvability_cuts', 'minimal_optimality_cuts']:
                self.assertIsNone(r[k])
        for key, pred in predicates.items():
            expected = [s for s in range(full + 1) if pred(s) and not any(pred(t) for t in range(s) if t & s == t)]
            self.assertEqual(r[key], expected, key)
        if solved:
            # Each minimal removed cut hits every minimal sufficient action set, and vice versa.
            for pkey, ckey in [('minimal_sufficient_enabled', 'minimal_solvability_cuts'), ('minimal_optimal_enabled', 'minimal_optimality_cuts')]:
                hits = [s for s in range(full + 1) if all(s & p for p in r[pkey])]
                minimal = [s for s in hits if not any(t != s and t & s == t for t in hits)]
                self.assertEqual(r[ckey], minimal)
        for a, row in enumerate(r['single_removals']):
            target = full ^ (1 << a)
            self.assertEqual(row, dict(action=a, enabled_mask=target,
                used_by_representative=a in table[full]['representative'] if solved else None,
                necessary_for_optimality=table[target]['distance'] != table[full]['distance'] if solved else None,
                necessary_for_solvability=table[target]['distance'] is None if solved else None))
        return r

    def test_controls_and_distinct_necessity(self):
        controls = json.loads((ROOT / 'docs/sensitivity-controls.json').read_text())
        for c in controls:
            self.check(c['input'])
        r = audit_sensitivity(controls[0]['input'])
        self.assertEqual(r['minimal_sufficient_enabled'], [1, 14, 16])
        self.assertEqual(r['minimal_optimality_cuts'], [17])
        self.assertEqual(r['minimal_solvability_cuts'], [19, 21, 25])
        self.assertEqual(r['scenarios'][14]['distance'], 3)
        self.assertTrue(r['single_removals'][0]['used_by_representative'])
        self.assertFalse(r['single_removals'][0]['necessary_for_optimality'])
        r = audit_sensitivity(controls[1]['input'])
        self.assertTrue(r['single_removals'][0]['necessary_for_optimality'])
        self.assertFalse(r['single_removals'][0]['necessary_for_solvability'])

    def test_seeded_and_boundary_certificates(self):
        rng = random.Random(23141)
        for _ in range(80):
            m = rng.randrange(4)
            fs = lambda: [f for f in range(m) if rng.randrange(2)]
            actions = []
            for _ in range(rng.randrange(7)):
                add = fs()
                actions.append(dict(pre=fs(), add=add, delete=[f for f in fs() if f not in add]))
            self.check(dict(facts=m, initial=fs(), goal=fs(), actions=actions))

    def test_strict_validation(self):
        for task in [{}, {'facts': True, 'initial': [], 'goal': [], 'actions': []}]:
            with self.assertRaises(ValueError):
                audit_sensitivity(task)
