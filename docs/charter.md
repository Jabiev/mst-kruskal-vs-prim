# Project Charter — T05: Minimum spanning trees, Kruskal vs Prim

_Lessons 1–2. Frozen at the checkpoint (lessons 3–4); any later change is listed in §13._

## Team
- Nurlan Jabiyev
- Gunel Rzayeva

## 1. Research question
How do edge density and graph structure, in synthetic and real-life graphs, affect the
runtime of Kruskal's and Prim's algorithms, and how much do union-find and heap
operations contribute?

**Final answer must show:** which algorithm is faster for which densities and structures,
including the real graph, and how much of each algorithm's time goes to sorting,
union-find and heap operations.

### Why this needs an experiment
Both algorithms always return a tree of the same total weight, so we compare **cost, not
result**. Theory does not settle it: Kruskal is O(E log E) and heap-based Prim is
O(E log V), but E ≤ V² gives log E ≤ 2 log V, so **both are Θ(E log V)**. The winner is
decided by constant factors (merge steps vs heap sifts, early termination, memory
access), which only measurement can show.

## 2. The real graph (A2, A5)

**Choice: the road network of central Baku, built by us from OpenStreetMap.**

| | |
|---|---|
| Source | OpenStreetMap, Overpass API (ODbL, © OpenStreetMap contributors) |
| Area | bounding box 40.35–40.44 N, 49.78–49.97 E |
| Size | **11 838 vertices** (intersections and dead ends), **15 117 edges** (street segments), average degree 2.55 |
| Weights | street segment length in **centimetres** |
| Obtained by | `python scripts/build_real_graph.py` (download, then conversion); result committed in `data/` with provenance in `data/baku_roads.json` |

**Why this graph suits the question.**
- An MST needs **meaningful weights**. A road has a physical length. Twitter and Wikipedia
  graphs are unweighted, so any weights there would be invented.
- The MST has a **real meaning** here: the shortest set of streets along which a cable
  (fibre, power) connects every intersection. This is the classic MST application.
- Road networks are a **structure no random generator reproduces**: planar, very sparse,
  local, with long chains. That is exactly the "structure" part of the question.
- It is **local** (Baku), reproducible (script + saved data), and small enough for
  Python while still realistic.

**Controlled size and density from the real data.**
- `road_ball(n, seed)`: a connected piece of the real road network with n intersections,
  grown by breadth-first search from a seeded start. Real structure, chosen size.
- `geo_knn(n, k, seed)`: n real intersections (seeded sample), each joined to its k
  nearest neighbours; weight = straight-line distance in cm (cost of a direct link).
  k = 4 is road-like, k = 256 is dense, k = n − 1 is the complete graph. Real positions,
  chosen density.

## 3. Decisions required by T05

### Decision 1: Which sorting algorithm, and why
**Bottom-up merge sort** (`src/mst/sorting.py`).
- **O(E log E) in every case.** Quicksort has an O(E²) worst case. With a two-way partition
  it degrades badly on **many equal keys**, and our synthetic weights 1..100 are full of ties.
- **Stable.** Equal weights keep their input order, so ties are broken identically on every
  run and the tree is reproducible.
- **Iterative.** No recursion, so no recursion limit on 150 000 edges.
- **Independent of the heap.** Heapsort would reuse the binary heap and mix "sort cost" with
  "heap cost", the two quantities we must separate.
- Rejected: counting/radix sort. It is near-linear on weights 1..100, but our real weights
  are centimetres up to several kilometres, and a radix sort would answer a different
  question (non-comparison sorting).

### Decision 2: What each union-find optimisation achieves
`UnionFind(n, by_rank, compress)` lets each optimisation be switched off independently,
giving four variants: **both**, **rank only**, **compression only**, **neither**. All four run
the same code, so differences come from the optimisation, not from different code.
The `unionfind` experiment runs Kruskal with each variant on the same instances and reports:
- `path_steps / find_calls`: average links followed per `find` (the direct effect)
- `union_find_s`: time of the union-find loop (the effect on runtime)
- a worst-case input (a chain built by naive linking) in the tests: 1 999 000 path steps
  without optimisations vs about 4 000 with either one

### Decision 3: Separating the sort time from the rest of Kruskal
`kruskal(graph, phase_times={})` reads `perf_counter` three times: before the sort, after the
sort, and after the union-find loop. This is done in a **separate instrumented run**; the
timed repetitions pass `phase_times=None`, so the timers never affect the reported
runtime. Shares are reported as `sort_s / (sort_s + union_find_s)`.

**Prim's heap time** (the same question for Prim): heap calls are interleaved with the
rest of the loop and are too short to time one by one. So the instrumented run uses a
`RecordingHeap` that stores the exact sequence of pushes and pops; that sequence is then
**replayed** on a fresh heap and timed, minus the time of the same loop without heap calls
(`src/bench/phases.py`). Heap share = `heap_s / median_s`.

### Decision 4: Turning the real graph into a valid MST input; meaning of the weights
1. Only drivable streets (OSM highway types motorway…residential, living_street, links).
2. **Undirected**: one-way tags ignored; a cable can be laid in either direction.
3. **Vertices = intersections and dead ends.** Shape points between them are merged into
   one edge whose weight is the summed great-circle (haversine) length.
4. **Self-loops removed** (5): a street returning to the same intersection is never in an MST.
5. **Parallel edges** (22): only the shortest is kept; a longer parallel edge is never in an MST.
6. **Largest connected component** kept (41 components; 117 vertices dropped), because an MST
   needs a connected graph and the bounding box cuts a few streets.
7. Weights **rounded to whole centimetres** (integers): totals are exact, so Kruskal and Prim
   can be compared with `==`, with no floating-point rounding issues.

**Meaning:** weight = length of street in cm; MST total = shortest street length that
connects all intersections (875.19 km out of 1 532.92 km of streets).

### Decision 5: Checking both results are MSTs although ties allow different trees
Comparing edge sets would be wrong (ties), and comparing totals needs a trusted reference. So:
- **Independent proof check** (`src/mst/verify.py`), our own code, no library:
  1. V − 1 edges and no cycle → spanning tree;
  2. every tree edge exists in the graph with that weight;
  3. reported total = sum of tree weights;
  4. **cycle property:** for every graph edge (u, v, w), the heaviest edge on the tree path
     u→v weighs ≤ w. A spanning tree is minimum **if and only if** this holds, *whatever*
     tie-breaking was used. Path maxima by binary lifting, O((V + E) log V).
- **Oracle:** `networkx.minimum_spanning_tree` total weight, **in tests only**.
- **Hand-checked** small graphs, including a square of four equal edges where all four
  possible MSTs are accepted and wrong trees are rejected.
- In the benchmark, **every** result is verified (outside timing), and the run stops if
  Kruskal's and Prim's totals ever differ.

## 4. Inputs, sizes, seeds and runs (A5)

| Family | Sizes / parameters | Instances |
|---|---|---|
| **road** (real) | full network (V = 11 838) | 1 |
| **road** pieces (real) | V = 1 000, 3 000, 10 000 | 10 seeds each |
| **geo_knn** (real positions) | V = 200, 500, 1 000 × k = 4, 16, 64, 256 (k < V) | 10 seeds each |
| random (control) | V = 200, 500, 1 000 × p = 0.01, 0.05, 0.20 | 10 seeds each |
| grid (control) | 32×32, 64×64, weights 1..100 | 10 seeds each |
| matched random (control) | exactly the grid's V and E | 10 seeds each |

- **Runs:** 1 untimed warm-up, then **7 timed repetitions**, median reported.
- **Caps:** 5 s and 256 MiB per run. An over-cap run is recorded as `timeout`/`memory`, never dropped.
- **Seeds:** 0–9, fixed; every generator uses its own `random.Random(seed)`.
- **Total time:** measured in the pilot run and written here: _pilot pending_.

## 5. Hypotheses (before any experiment)

| # | Hypothesis | Refuted if… |
|---|---|---|
| H1 | On the sparse road network and its pieces, **Kruskal is faster**. | Prim's median is lower on most instances. |
| H2 | As density grows (k, p), **Prim's advantage grows**: the Kruskal/Prim time ratio increases with density at every V. | The ratio does not increase with density. |
| H3 | **Sorting is the largest part of Kruskal's time** (> 50 %), and its share grows with density. | Sort share ≤ 50 % on most instances, or does not grow. |
| H4 | With both optimisations, path steps per `find` stay **below 2**. Without either, they grow with V, and each optimisation alone removes most of the gap. | Mean ≥ 2 with both, or a single optimisation leaves most of the gap. |
| H5 | **Heap operations are the largest part of Prim's time** (> 50 %); the stale-pop ratio grows with density. | Heap share ≤ 50 %, or stale ratio does not grow. |
| H6 | At equal V and E, grid vs matched random changes runtime by **less than 10 %**. | Median difference ≥ 10 % and larger than run-to-run spread. |
| H7 | The real road network **behaves like the grid** (same winner, similar ratio), because both are sparse and local. | A different winner on road pieces vs grids of similar V. |

A refuted hypothesis is still a valid result if the method is rigorous.

## 6. Components: interfaces and expected complexity (A3)

| Component | Interface | Expected complexity |
|---|---|---|
| `Graph` | `Graph(n)`, `add_edge(u, v, w)`, `neighbors(u)`, `edges()`, `num_vertices()`, `num_edges()` | O(n) create; O(1) add; O(deg u) neighbours; O(E) edges; O(1) sizes |
| `merge_sort` | `merge_sort(items, key) -> new sorted list`, stable | O(E log E) time, O(E) extra memory |
| `BinaryHeap` | `push(item)`, `pop() -> smallest` (IndexError if empty), `len()` | O(log n) push and pop |
| `UnionFind` | `UnionFind(n, by_rank, compress)`, `find(x)`, `union(x, y) -> bool` | both: O(α(n)) amortised; one: O(log n) amortised; neither: O(n) worst |
| `kruskal` | `kruskal(graph, phase_times=None, by_rank, compress) -> (edges, total, counters)` | O(E log E) |
| `prim` | `prim(graph, start=0, heap=None) -> (edges, total, counters)` | O(E log E) = O(E log V) |
| `verify_mst` | `verify_mst(graph, edges, total) -> True` or raises `NotAnMST` | O((V + E) log V) |
| generators | `random_graph(n, p, seed)`, `random_graph_m(n, m, seed)`, `grid_graph(r, c, seed)`, `road_ball(n, seed)`, `geo_knn(n, k, seed)` | O(n²) random; O(V + E) grid, road; O(n² log n) geo_knn (outside timing) |

Both algorithms read the graph only through the `Graph` interface. Disconnected input
raises `ValueError` in both.

## 7. Counters: exact definitions (A4)

| Counter | Definition |
|---|---|
| `find_calls` | number of calls to `UnionFind.find` (two per edge examined, from `union`) |
| `path_steps` | parent links followed in the first pass of `find` (from x up to the root), summed over all calls |
| `unions` | `union` calls that merged two different sets (= V − 1 for a connected graph) |
| `edges_scanned` | sorted edges examined by Kruskal before V − 1 were accepted |
| `pushes` | `BinaryHeap.push` calls in Prim |
| `pops` | `BinaryHeap.pop` calls in Prim |
| `stale_pops` | pops whose vertex was already in the tree (skipped); `pops = (V − 1) + stale_pops` |
| `sort_s`, `union_find_s` | Kruskal phase times from the instrumented run (§3, decision 3) |
| `heap_s` | Prim heap time from the replay (§3, decision 3) |
| `median_s` | median of the 7 timed repetitions of the whole algorithm call |
| `peak_mib` | peak traced memory of one run under `tracemalloc` (separate, untimed run) |

## 8. Correctness before timing
All tests must pass before any benchmark (`python -m pytest`): hand-checked graphs,
`networkx` oracle, the proof check of decision 5 on every family (including the full real
graph), edge cases (one vertex, parallel edges, disconnected input, all-equal weights),
our sort vs Python's `sorted`, our heap vs `heapq` on 5 000 random operations, and counter
invariants.

## 9. Timing protocol (A4)
- Graphs generated **outside** the timed part; both methods on **the same instance**.
- 1 untimed warm-up, 7 timed repetitions with `time.perf_counter`, **median**.
- Garbage collector disabled during timed repetitions (as `timeit` does).
- Method order alternates by seed, so neither method always runs first.
- Memory, phase times and verification each run separately from the timed repetitions.

## 10. Statistical analysis (A4)
- For each setting: the **distribution over the 10 seeds** (median, IQR, box plots), not one number.
- **Paired comparison:** per instance, the ratio Kruskal time / Prim time. Across seeds, a
  Wilcoxon signed-rank test on the paired times.
- **Larger than run-to-run variation?** Per instance, the spread of the 7 repetitions
  ((max − min) / median) is compared with the difference between the methods; a difference
  inside that spread is reported as "no clear winner".
- Shares (sort, union-find, heap) reported as distributions over seeds.

## 11. Environment
- Python 3.12.10 (CPython, python.org build), Windows 11 Pro
- CPU / RAM: _to be added_
- Every benchmark writes its environment next to its CSV (`results/*.json`).

## 12. Milestones
| Lessons | Goal |
|---|---|
| 1–2 | Charter: research question, predictions, chosen graph, ADT contracts |
| 3–4 | Baselines + correctness tests; oral checkpoint (design slides + prototype); **protocol frozen** |
| 5–6 | Pilot run (scope and time budget), then main runs and analysis |
| 7–8 | Final results and answer; individual defence |

## 13. Implementation decisions and changes
| Decision | Reason |
|---|---|
| Graph stores both an adjacency list and an edge list, built before timing | each algorithm reads its natural form; no conversion inside the timed part |
| Kruskal stops scanning after V − 1 accepted edges | standard early exit; the full sort is still paid, so H3 is unaffected |
| Prim pushes only edges to vertices not yet in the tree | fewer useless pushes; stale pops still happen and are counted |
| GC disabled during timed repetitions | removes random collector pauses |
| Caps checked after each run | Python cannot safely interrupt a running function; an over-cap run is recorded and remaining reps skipped |
| Real graph measured once (one fixed instance); its pieces with 10 seeds | the full network has no randomness; seeds apply to derived inputs |

_Changes after the freeze: none yet._

## 14. Risks
| Risk | Plan |
|---|---|
| Tied weights give different trees | proof check (decision 5), never edge-set comparison |
| Sorting left outside timing | sort inside `kruskal()` |
| Phase timers distort runtimes | phases only in separate instrumented runs |
| OpenStreetMap changes over time | converted graph committed in `data/`, with download timestamp |
| Background processes add noise | median of 7, 10 seeds, spread reported |
| Runs exceed 5 s | recorded as timeout, kept in results |
