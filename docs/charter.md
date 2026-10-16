# Project Charter — T05: Kruskal vs Prim

_Sessions 1–3._

## Team
- Nurlan Jabiyev
- _partner_

## 1. Aim — what we want to find out

Kruskal and Prim always return a minimum spanning tree with the **same total weight**.
So the interesting question is **not *what* they compute but *how much it costs*, and why.**

> **Aim.** Measure how **edge density** and **graph structure** decide which MST algorithm
> is faster in practice, and find out **which internal operation actually dominates the
> cost**: sorting, union-find, or the heap. Then check whether the textbook Big-O
> explanation matches what we measure.

### Why this is worth exploring (not just "look up the answer")

1. **Theory hardly separates the two.** Kruskal is O(E log E) and heap-based Prim is
   O(E log V). Because E ≤ V², log E ≤ 2 log V, so **both are Θ(E log V)**. Big-O
   does not tell us who wins. Constant factors and data structures do, and only
   an experiment can show them.
2. **The "obvious" bottleneck may be wrong in Python.** Textbooks say Kruskal's cost is
   the sort. But Python's `sorted()` runs in optimised C, while our union-find runs as
   Python code. The real bottleneck could be union-find, not sorting. We want to *measure*
   this rather than assume it.
3. **Prim's lazy heap wastes work.** With lazy deletion, every edge to an already-visited
   vertex leaves a *stale* heap entry. On dense graphs most pops could be stale. How
   much of Prim's time is wasted this way?
4. **Density is not the whole story.** A grid and a random graph can have the same V and E
   but very different shapes (short local cycles vs long random ones). Does structure
   change the result when the size is the same?

## 2. Research questions

| # | Question | Answered by |
|---|---|---|
| **RQ1** | **Crossover:** as density p grows (V fixed), does the faster algorithm change, and at what density? | Median runtime vs p for each V |
| **RQ2** | **Cost breakdown:** what share of Kruskal's time is sorting vs union-find? What share of Prim's pops are stale? | Phase timing (separate instrumented run) + counters |
| **RQ3** | **Structure:** at equal V and E, do grid and random graphs give different results? | Grid vs a random graph with the *same* V and E |
| **RQ4** | **Theory vs practice:** does runtime grow like E log V as predicted? | Runtime / (E log V) across sizes; should be roughly flat |

## 3. Hypotheses (written before any experiment, each one can be proven wrong)

| # | Hypothesis | We call it **refuted** if… |
|---|---|---|
| H1 | Kruskal is faster on sparse graphs (p = 0.01, grids). | Prim's median is lower in most seeds at p = 0.01. |
| H2 | As p grows, Prim catches up; a crossover may exist but need not, because both are Θ(E log V). | Reported either way: the crossover p, or "no crossover in range". |
| H3 | In Python, **union-find, not sorting**, takes the larger share of Kruskal's time. | Sort phase > 50 % of Kruskal's time. |
| H4 | Union-find stays cheap: average path steps per `find` stay below 2. | Mean path steps per `find` ≥ 2 at any size. |
| H5 | Prim's stale-pop ratio rises with density (most pops are stale at p = 0.20). | Stale ratio does not grow with p. |
| H6 | At equal V and E, grid vs random structure changes runtime by less than 10 %. | Median difference ≥ 10 %. |

A refuted hypothesis is still a valid result if the method is rigorous.

## 4. Application (why anyone cares)
Cheapest network connecting all sites (cables, pipelines, roads), single-linkage
clustering, and approximation of the travelling-salesman problem. In practice the input
is often very sparse (road networks, grids) or very dense (all-pairs distances between
points), which is exactly the density range we vary.

## 5. Scope: what we do **not** claim
- Results are for **Python 3.12 on our laptops**. We claim relative behaviour, not
  absolute speed in other languages.
- Integer weights 1..100, so **ties are frequent**: edge sets may differ, total weight may not.
- Fibonacci-heap Prim is out of scope (theoretical interest only, slow in practice).

## 6. Graph ADT contract
| Operation | Meaning | Expected cost |
|---|---|---|
| `Graph(n)` | empty graph with vertices `0..n-1` | O(n) |
| `add_edge(u, v, w)` | undirected edge with integer weight `w` | O(1) |
| `neighbors(u)` | iterable of `(v, w)` pairs | O(deg u) |
| `edges()` | iterable of `(u, v, w)`, each edge once | O(E) |
| `num_vertices()`, `num_edges()` | sizes | O(1) |

Both algorithms read the graph **only through this contract**, so neither gets a
representation advantage.

## 7. Methods
- **Kruskal:** sort edges (inside the timed part) + union-find (union by rank, path compression).
- **Prim:** `heapq` with lazy deletion (stale entries skipped and counted).

## 8. Experimental design
| Factor | Values |
|---|---|
| Random graphs, V | 200, 500, 1000 |
| Edge probability p | 0.01, 0.05, 0.20 |
| Grid graphs | 32×32, 64×64 |
| **Matched random graphs (RQ3)** | same V and E as each grid |
| Weights | uniform integers 1..100 |
| Connectivity | random spanning tree first, then extra edges |
| Seeds | 10 per setting |

- **Timing:** graphs generated outside timing · 1 untimed warm-up · 7 timed repetitions ·
  median · 5 s and 256 MiB caps · timeouts kept and reported.
- **Same instances:** both algorithms run on exactly the same graph object per seed.
- **Phase timing (RQ2)** is measured in a *separate* instrumented run, so the extra
  timers never disturb the main timing.
- Sizes may be adjusted for our laptops; any change is recorded here with its reason.

### Implementation decisions
| Decision | Reason |
|---|---|
| Graph stores **both** an adjacency list and an edge list, built once before timing | Each algorithm reads its natural form; neither pays a conversion inside the timed part |
| Kruskal **stops scanning** after V − 1 accepted edges | Standard early exit; the full sort is still paid, so H3 is unaffected |
| Prim pushes only edges to vertices **not yet in the tree** | Fewer useless pushes; stale pops still happen and are counted |
| Garbage collector **disabled** during timed repetitions | Same choice as Python's `timeit`; removes random GC pauses |
| Caps are checked **after** each run | Python cannot safely interrupt a running function; an over-cap run is recorded as `timeout` and remaining reps are skipped |
| Peak memory measured in a **separate** `tracemalloc` run | `tracemalloc` slows code down, so it must not overlap with timing |
| Method order **alternates** by seed | Neither algorithm always runs first (cache / CPU warm-state bias) |
| Matched random graph uses **exactly** the grid's V and E | RQ3: only structure differs |

## 9. Measurements
| Measurement | Used for |
|---|---|
| Median runtime | RQ1, RQ3, RQ4 |
| Kruskal sort time vs union-find time | RQ2, H3 |
| `find` calls, path steps, unions (= V − 1) | RQ2, H4 |
| Heap pushes, pops, stale pops | RQ2, H5 |
| Total MST weight | correctness: must be identical for both |

## 10. Correctness check (before any timing)
Same total weight for both · V − 1 edges · all vertices connected · hand-checked small
graphs · `networkx` used as an independent oracle **in tests only**.

## 11. Environment
- Python version: 3.12.10
- OS / laptop: Windows 11 Pro · _CPU / RAM: fill in_

## 12. Risks
| Risk | Plan |
|---|---|
| Tied weights give different edge sets | Compare total weights, not edge sets |
| Sorting accidentally left outside timing | Sort inside `kruskal()` |
| Phase timers distort runtimes | Phase timing only in a separate instrumented run |
| Background processes add noise | Median of 7, 10 seeds, report spread (IQR) |
| Runs exceed 5 s | Record as timeout, keep in results |
