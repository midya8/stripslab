# STRIPSLab static action-availability witnesses

## Three different claims

A displayed representative plan is only one plan. An action in it need not occur in every shortest plan. An action occurring in every shortest plan need not occur in every successful plan. This extension answers those questions exactly for the existing finite positive unit-cost STRIPS task, by enumerating every static subset of available action IDs.

Availability is fixed for an entire plan. Disabling an action removes every use of that original ID. The initial world, goal, preconditions and effects do not change. Duplicate action definitions keep different IDs. This is deterministic re-planning, not an estimate of failure probability or a simulation of timed outages.

## Certificate

`audit_sensitivity(task)` retains the entire unchanged base audit plus one scenario for every enabled-action bitmask, in ascending mask order. Each scenario has:

- Enabled and removed original action IDs.
- Exact initial goal distance, exact decimal-string shortest action-sequence count and lexicographically smallest shortest action-index sequence.
- Forward distance from the initial state and backward distance to any goal for every world state, including unreachable world states.
- The number of shortest initial prefixes to every world state, as a decimal string.
- Every edge on any shortest initial-to-goal plan, in ascending source/action order.

Null distance means unreachable, not zero. Unsolvable scenarios have null representative and count `"0"`. An already satisfied goal has distance zero, one empty shortest plan and no optimal edges. Self-loops and cycles do not create extra shortest paths. Prefix counts are not goal-plan participation counts.

Python uses forward/reverse queue-based BFS and integer DAG counts. Independently written JavaScript uses synchronous all-state distance sweeps, then BigInt counts in distance layers. Both reconstruct the lexicographically smallest representative by following the smallest original action ID that decreases exact remaining distance. Neither implementation calls the other's planner. All action and state identifiers retain the original task's meaning; an action-availability mask is not a world-state fact mask.

## Complete monotone boundaries

Adding available actions cannot remove a plan that already exists. Solvability and preservation of the all-actions baseline optimum are therefore monotone predicates on enabled sets. The audit reports:

1. All inclusion-minimal sufficient enabled sets.
2. All inclusion-minimal enabled sets preserving the baseline optimum.
3. All inclusion-minimal removed sets that destroy solvability.
4. All inclusion-minimal removed sets that destroy the baseline optimum, including making the task unsolvable.

Minimal means inclusion-minimal, not minimum cardinality. For monotone predicates it is sufficient to inspect every one-element deletion for minimality; native tests independently compare all proper subsets. The minimal sufficient sets and minimal removal cuts are mutual minimal hitting sets. Native tests enumerate hitting sets independently in both the solvability and optimum-preserving cases.

For a solvable baseline, every valid plan contains at least one action from each solvability cut. These are inclusion-minimal disjunctive action landmarks for the actual task, not merely for its delete relaxation. An optimality cut guarantees intersection only for baseline-optimal plans; it is not generally a landmark for every valid plan. No LM-cut heuristic, landmark ordering, cost partitioning or scalable landmark extraction algorithm is implemented.

When the baseline is already unsolvable, the sufficient family is empty and the other three families and all necessity claims are null. This avoids presenting vacuous all-plan assertions as useful necessity. When the goal is initially satisfied, the sufficient and optimum-preserving families contain the empty set, and both cut families are empty. No action is necessary for the empty plan. These boundary conventions are explicit extensions beyond ordinary nondegenerate reliability-system assumptions.

The single-removal table separately records whether each original action occurs in the representative, is required for baseline optimality, or is required for solvability. A representative-use flag never substitutes for a necessity test.

## Original controls

The main three-fact task has two distinct one-action shortcuts to the goal and a separate three-action detour. The representative uses action 0, but neither shortcut is individually required. Removing both shortcuts destroys optimality but leaves the longer plan. Destroying solvability also requires removing one detour action. The minimal sufficient enabled masks are 1, 14 and 16; the minimal optimum-destroying removed mask is 17; the minimal solvability-destroying removed masks are 19, 21 and 25. Masks retain original action IDs.

A second control removes the duplicate shortcut. Its sole shortcut is required by every shortest plan but not every successful plan. A third exercises the hard bound of six facts/eight actions with duplicate shortcuts and a six-action detour. The remaining controls retain every base and search task, including hidden dead ends, restored resources, duplicate IDs, empty goals and cyclic prerequisites. No paper graph or published planning benchmark is copied.

## Validation and reproduction

Eighteen controls retain 466 availability scenarios, 21,731 per-scenario state rows and 408 initial-optimal-plan edges. These are fixture coverage counts, not performance results. Native reference tests rebuild transitions directly using sets and independently count paths by layers, choose lexicographic witnesses and validate every distance, count, edge, original ID and boundary. They cover all controls plus 80 seeded tasks. JavaScript compares complete certificates on all controls and a different 100-task seeded bank. The browser checks every scenario, every state row, optimal edge, replay, family, single-removal claim, JSON record, export and invalid-input clearing. Every retained scenario is layout-checked at 320/390/1280.

```sh
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
python -m stripslab --sensitivity examples/task.json
stripslab --sensitivity examples/task.json -o availability.json
```

`--search` and `--sensitivity` are mutually exclusive. The original default mode is unchanged. Strict UTF-8, duplicate/nonfinite JSON, input byte bounds and atomic output replacement remain in force. Native and browser parser differences from METHOD.md still apply. Isolated wheel reproduction checks fourteen base, fifteen search and eighteen availability reports, five installed module origins and both CLI entry points in all three modes.

## Sources and inspected coverage

The seven source groups in [METHOD.md](METHOD.md) ground STRIPS, graph distances, plan counting and delete relaxation. The two search-policy sources in [SEARCH.md](SEARCH.md) ground the separate search inspector. Three additional sources were discovered by public search and fetched for this extension:

- Alvaro Torralba and Cosmina Croitoru, Saarland University, *AI Planning: Landmark Heuristics*, winter 2018/2019, with slide-source credit to Joerg Hoffmann. Inspected introduction, fact/disjunctive action landmark definitions, inclusion-minimality and induced-vs-general landmark sections. Supports landmark terminology, not the claim that this exhaustive procedure scales. No lecture task or figure copied. https://fai.cs.uni-saarland.de/teaching/winter18-19/planning-material/planning14-landmark-heuristics-pre-handout.pdf
- University of Basel, *A Beginner's Introduction to Heuristic Search Planning: Delete Relaxation and Landmarks*, AAAI 2015 tutorial. Inspected relaxed-task notation and landmark/hitting-set definitions. The tutorial's cost partitioning, justification graphs and LM-cut methods are not implemented. No weighted example copied. https://ai.dmi.unibas.ch/misc/tutorial_aaai2015/planning06.pdf
- Jean-Luc Marichal, University of Luxembourg, *Structure functions and minimal path sets*, revised September 30, 2015. Inspected introduction/Boolean subset identification, minimal path definition and section 2's minimal cut definition and duality discussion. Supports monotone-set boundary terminology. Extracted formulas have damaged notation, so no numerical polynomial or reliability formula is reproduced. This project neither supplies component probabilities nor claims the paper's nondegenerate semicoherent-system assumptions for empty-goal/unsolvable cases. https://orbilu.uni.lu/bitstream/10993/23215/1/StructureFunctionsMinimalPathSets.pdf

This is an original bounded educational implementation of established graph search and monotone-set enumeration. At most six facts/eight grounded positive-precondition unit-cost actions: 64 states and 256 subsets. No PDDL, real-world execution, temporal/conditional failure, stochastic reliability, benchmark win, runtime speedup, novel algorithm, learned model or safety guarantee is claimed.
