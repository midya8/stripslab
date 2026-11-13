# STRIPSLab

STRIPSLab compares real and delete-relaxed plans for small positive STRIPS tasks,
using independent Python and JavaScript implementations. Inspect every state, every blocked/applicable action, every shortest-plan choice and every delete-relaxation failure witness. No model, API or runtime package dependency.

[Live inspector](https://midya8.github.io/stripslab/) | [Method and prior work](METHOD.md)

## Choose a calculation

- **State audit:** compare exact real and relaxed goal distances, shortest plans and heuristic costs for every state.
- **Search:** inspect how zero, h-max, h-add and exact h-plus order the frontier and what plan each search returns.
- **Action availability:** remove static subsets of actions and distinguish representative use from necessity for an optimum or for any solution.

The current suite has 17 Python tests and 9 Node/Chrome tests across all three inspectors.

A relaxed plan can exist when no real plan does. A heuristic's expansion count
also excludes its precomputation cost, so it is not a runtime comparison.

## State audit

- All 2^m fully known states, all missing preconditions and real/relaxed successors, with actual added/removed facts.
- Reachability from the supplied initial state, plus exact remaining real and relaxed goal distance from every state independently.
- Complete real and delete-relaxed shortest suffix DAGs, all action ties, exact decimal-string sequence counts and deterministic representative plans.
- Every edge on any initial shortest plan, with full representative state replays in both worlds.
- h-max and h-add fact-cost fixed points, every synchronous round including final stability, and all tied best fact achievers.
- Explicit hidden dead ends and h-add overestimation witnesses. Null never means zero; an already satisfied goal has one empty shortest plan.

Fourteen original synthetic tasks cover 127 states, 524 state/action checks, 36 initial optimal-plan edges, 50 initially reachable states and 866 fixed-point round vectors. Controls expose additive double counting, relaxed solvability without any real plan, a restoration cost omitted by relaxation, max ignoring combined effort, six shortest action orders, duplicate action identities, empty universes, cyclic prerequisites, irreversible traps and no-op loops.

## Reproduce

```sh
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
python -m stripslab examples/task.json
python -m stripslab examples/task.json -o audit.json
```

Python 3.10-3.13, Node 22 and Chrome for browser tests. `uv` builds an isolated wheel for the installed reproduction check. The runtime library itself uses only the Python standard library. Serve `docs` with a local HTTP server for the browser inspector.

```sh
python -m pip install .
stripslab examples/task.json
python -m http.server --directory docs 8000
```

The original eight native tests check set-based all-pairs shortest paths, independent bounded-walk sequence counts, recursive relaxed derivation costs, every round and every achiever; exhaustive tiny tasks and deterministic seeded tasks accompany retained controls. The original three Node/actual-Chrome tests compare complete independent reports, every retained UI record, replay, export, invalid-edit clearing and all tasks at 320/390/1280. Installed checks compare 14 complete reports outside the checkout, three installed module origins and both console/module CLIs. CI also regenerates fixtures and checks exact equality.

## Input

```json
{"facts":3,"initial":[0],"goal":[1,2],"actions":[{"pre":[0],"add":[1],"delete":[0]},{"pre":[0],"add":[2],"delete":[0]}]}
```

This task is unsolvable: either action consumes fact 0. Ignoring deletes creates a two-action relaxed plan, which is not a real plan. All action costs are one. Positive goals/preconditions only. Add and delete must be disjoint, and fact lists must be unique valid indices. At most six facts/eight grounded actions. Action indices are identities, including duplicates. Details and parser differences are in METHOD.md.

## Scope and limits

Established planning theory, original bounded implementation and synthetic tasks. No PDDL parser/grounder, negative preconditions, conditional effects, costs other than one, concurrency, probabilistic outcomes, partial observability, real-world execution or safety guarantee. Exhaustive all-state auditing is exponential, not a scalable planner or benchmark claim. h-add is not admissible; finite relaxed values do not prove real solvability. Existing theory and software are attributed in METHOD.md. No external planner implementation, dataset or sample task is copied.


## Search: suboptimal h-add example

[Live search inspector](https://midya8.github.io/stripslab/search.html) | [Search method and sources](SEARCH.md)

Keep the complete state audit and compare zero/h-max/h-add/exact-h-plus search ordering. Inspect every valid frontier, selected label, applicable-action improvement, reopening, returned replay and termination. A new original control returns a three-action h-add plan when the real optimum is two. Exact h-plus is a full relaxed-graph oracle; all estimates are precomputed, so expansion counts are not runtime-speed measurements. Fixed ascending f/g/state-mask ties, goal-pop termination and strict g improvements are explicit.

Fifteen retained search tasks, 60 runs, 207 selected labels and 415 action decisions. The search release checked thirteen native tests on Python 3.10-3.13, six Node/Chrome tests, and installed-wheel reproduction of fourteen base plus fifteen search reports. Four installed module origins; both CLIs in both modes. Base inspector and original tests remain intact.

```sh
python -m stripslab --search examples/task.json
stripslab --search examples/task.json -o search-audit.json
```


## Static action availability

[Availability inspector](https://midya8.github.io/stripslab/sensitivity.html) | [Policy, controls and sources](SENSITIVITY.md)

A representative action is not automatically necessary. Enumerate every static action subset and distinguish representative use, necessity for the baseline optimum and necessity for any successful plan. Retain all minimal sufficient sets and all minimal solvability/optimality cuts, with every counterfactual distance, exact plan count, representative and optimal edge. Eighteen controls cover 466 scenarios and 21,731 state rows. Independent Python BFS and JavaScript distance sweeps reproduce complete reports. No probabilities, timed outages or real-world reliability score.

`python -m stripslab --sensitivity examples/task.json` exports the complete bounded certificate. Existing default and `--search` modes remain intact.
