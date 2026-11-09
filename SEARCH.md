# STRIPSLab search witnesses

## Established algorithm, original bounded certificate

This extension implements ordinary deterministic graph-search ordering by f = g + h over the existing positive unit-cost STRIPS world. It is an original educational implementation, not a new A* variant. The base inspector and all its complete shortest-plan families remain intact. Python uses a heap with obsolete labels skipped internally; independently written JavaScript uses a unique-state Map and linear frontier sorting. These implementation details do not become search steps: the public certificate retains every valid selected label and its complete valid frontier.

The four fixed estimates are zero, h-max, h-add and exact h-plus. All are computed by the full finite-world audit before search begins. h-plus is an expensive exact relaxed-graph oracle, not a cheap relaxed-plan approximation. Exact real distances are used only for after-the-fact diagnostics, never for ordering. This design is deliberately a small-world audit, not an end-to-end planning-performance experiment.

## Exact policy

1. The start has g = 0 and an empty action path. Other states are undiscovered, represented by null in final best-g output.
2. Sort valid frontier labels by ascending f, ascending g, then ascending state mask. Null h and f denote infinity and sort after finite values. This is a fixed lower-g tie policy, not FIFO breadth-first order, nor a claim about the best possible A* tie-break.
3. Remove the first valid label. Test the goal now, not when an action first generates a goal. A goal is selected but not expanded; its action-event list is empty.
4. For a non-goal, consider every applicable action in its original index order. Candidate g is selected g + 1. Record the previous known g, whether the candidate is a strict improvement, and whether it reopens a previously expanded state currently outside the frontier.
5. Insert or replace a label only on a strict g improvement. Equal-cost alternatives do not replace the stored path. Each label stores its own complete path, so a later improvement to some other label cannot silently rewrite an earlier returned path. Duplicate action definitions retain their positions but need not produce multiple frontier labels.
6. A previously expanded state can reopen on a strict improvement. Updating a label already in the frontier is an improvement but not a reopening. Terminate on a selected goal or an empty frontier. No infinite-estimate dead-end pruning is applied.

Every step retains the sorted frontier before selection, selected state/g/h/f, goal decision and every applicable-action improvement event. The report retains the final remaining frontier, final best discovered costs, per-state expansion counts, generated-label count, reopening count, returned path/cost, termination, exact initial optimum and regret. Generated includes the start plus each strict improvement. Expansions count non-goal selections, including repeat expansions. There is no stale-heap-pop count because the independent Map implementation has no stale entries.

Finite positive unit costs and strict improvements bound the search. A solved path is not a certificate of optimality with an inadmissible estimate. The all-state audit separately records admissibility and consistency violations against exact distances and every real applicable edge. Infinity is treated as an extended nonnegative cost: infinity is no larger than infinity, but exceeds every finite cost. Infinite real distance cannot be overestimated; an infinite heuristic at a finite-distance state would violate admissibility. The zero/h-max/h-plus runs are checked against exact optimality across all retained and generated tasks. No universal h-add optimality guarantee is claimed.

## Strict failure control

The original four-fact/five-action task has goals 0,1,2. One action adds helper fact 3; another requires 3 and adds all three goals. Three other actions each add one goal directly. The optimum is two actions via the helper. h-add values each direct goal as one. Under the disclosed tie policy, it follows the direct route and selects a three-action goal before taking the two-action shared route. The certificate retains cost 3, optimum 2 and regret 1. Zero, h-max and exact h-plus return cost 2. This is stronger than merely showing an overestimate; it is one concrete returned suboptimal plan, not a claim that h-add always fails.

Fifteen retained tasks consist of this new task and all fourteen base controls. They cover 60 runs, 207 selected labels, 415 applicable-action decisions and 433 frontier-label rows. These are fixture coverage counts, not benchmark results. Initially satisfied goals retain a single selected empty-plan goal with zero expansions. Unsolvable tasks terminate only when the frontier empties, with null returned plan/cost.

A separate original fixture in examples/search-reopen.json provides an admissible but inconsistent synthetic heuristic vector on a four-fact task. It causes a closed-state reopening while retaining an optimal returned plan. It tests the internal reopening mechanism and does not pretend to be one of the four public heuristic formulas. No example from a cited paper or lecture is copied.

## Validation and reproduction

Native certificate replay rebuilds transitions directly with sets and independently maintains frontier, discovered costs, paths and expansion history. It checks every complete frontier, minimum choice, action decision, final label, returned path, exact diagnostic and work count. It covers all fifteen controls and 120 seeded tasks with up to four facts/eight actions. The reopening fixture independently exercises strict-improvement reopening under an admissible inconsistent vector. JavaScript compares complete reports with Python on the fifteen controls and a different 140-task seeded bank. Base reference tests remain unchanged.

Chrome checks all 60 runs and every retained UI frontier, action event, selected-step record, returned replay, run/comparison/property table, final frontier and export. Invalid input edits clear and hide the stale certificate and disable export. All fifteen tasks in all four modes are layout-checked at 320/390/1280. The native/browser parser differences disclosed in METHOD.md still apply.

Run:

```sh
python -m unittest discover -s tests -v
npm test
bash tools/wheel_smoke.sh
python -m stripslab --search examples/task.json
stripslab --search examples/task.json -o search-audit.json
```

The wheel check runs outside the checkout, reproduces fourteen complete base reports plus fifteen complete search reports, verifies four installed module origins and checks both CLI entry points in both modes. Strict UTF-8/duplicate/nonfinite/byte-bound checks and atomic output replacement also apply to --search. The original default CLI mode is unchanged.

## Sources and coverage

The seven source groups in [METHOD.md](METHOD.md) ground STRIPS and the four estimates. Two additional sources were discovered by public search and directly fetched for the search-policy extension:

1. Andrew W. Moore, Carnegie Mellon University, `A* Heuristic Search` teaching slides. Inspected basic f = g + h definition, goal-pop termination, improved-path/revisit handling and admissibility sections (slides 3-12). Supports the algorithmic policy, not performance claims. Richer weighted graph examples, IDA* and slide figures are not copied or implemented. https://cs.cmu.edu/~cga/ai-course/astar.pdf
2. Robert C. Holte, *Common Misconceptions Concerning Heuristic Search*, SoCS 2009. Inspected abstract/introduction/background, discussion of tie-breaking and repeated expansion, and opening of the section on A* expansion optimality. Supports the distinction between returned-path optimality, expansion counts, tie policies and inconsistent-heuristic reopening. Extracted mathematical notation is degraded; exact implementation equations are grounded in source 1 plus the base planning sources. No paper graph, theorem-strength performance claim, IDA*, pathmax or bidirectional algorithm is reproduced. https://ai.dmi.unibas.ch/research/reading_group/holte-socs2009.pdf

The source set spans primary papers, teaching materials and official planner documentation. Source reading is section-specific, not a claim of reviewing every page. Six facts/eight grounded positive-precondition unit-cost actions remain the hard limit. No PDDL, learned heuristic, scalability, runtime speedup, benchmark win, real-world execution or new-algorithm claim.
