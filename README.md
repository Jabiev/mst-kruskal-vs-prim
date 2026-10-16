# Kruskal vs Prim — When Does Each MST Algorithm Win?

**Project Work 1 · T05** — M1 Data Science and Artificial Intelligence · UFAZ ·
Advanced Data Structures and Algorithms · Fall 2026

Team: Nurlan Jabiyev · Gunel Rzazade

---

## 1. Aim

> Both Kruskal and Prim always find the **same cheapest network** connecting every vertex.
> So we compare **cost, not result**: **which one is faster, on which kind of graph, and
> which internal part (sorting, union-find, heap) is really responsible?**

Why this needs an experiment: Big-O does not decide it. Kruskal is O(E log E) and heap-Prim
is O(E log V), and since E ≤ V², **both are Θ(E log V)**. In Python the "obvious" bottleneck
(sorting) runs in C, while union-find runs as Python code, so the textbook explanation may
not match reality.

**Research questions:** RQ1 crossover density · RQ2 cost breakdown (sort vs union-find,
stale heap pops) · RQ3 structure at equal size (grid vs random) · RQ4 does runtime scale
like E log V. Full aim, hypotheses and refutation criteria: [`docs/charter.md`](docs/charter.md).

## 2. The two methods

| | **Kruskal** | **Prim** |
|---|---|---|
| Idea | Sort **all** edges cheapest-first; add an edge unless it makes a loop | Start at one vertex; repeatedly add the cheapest edge reaching a **new** vertex |
| Helper structure | **Union-find** (union by rank + path compression) detects loops | **Binary heap** (`heapq`, lazy deletion) picks the cheapest edge |
| Cost | O(E log E) — dominated by the sort | O(E log V) — dominated by heap operations |

## 3. Prediction (written before any experiment)

1. **H1 Sparse graphs:** Kruskal is faster.
2. **H2 Dense graphs:** Prim catches up; a crossover may exist, but need not (both Θ(E log V)).
3. **H3 Bottleneck:** in Python, union-find, not sorting, takes most of Kruskal's time.
4. **H4 Union-find stays cheap:** average path steps per `find` stay below 2.
5. **H5 Prim's waste:** the stale-pop ratio grows with density.
6. **H6 Structure:** at equal V and E, grid vs random changes runtime by less than 10 %.

A result that contradicts any of these is still a valid result if the method is rigorous.

## 4. Experiment design

| Factor | Values |
|---|---|
| Random graphs, vertices V | 200, 500, 1000 |
| Edge probability p | 0.01, 0.05, 0.20 |
| Grid graphs | 32×32, 64×64 |
| Matched random graphs | same V and E as each grid (isolates structure from size) |
| Weights | uniform integers 1..100 |
| Connectivity | a random spanning tree is built first, then extra edges added |
| Seeds | 10 per setting |

**Timing protocol (from the catalogue):** graphs generated *outside* the timed part ·
1 untimed warm-up · 7 timed repetitions · record the **median** · cap 5 s and 256 MiB per run ·
timeouts are kept and discussed, never deleted. **Sorting is inside Kruskal's timed part.**

## 5. What we measure

| Measurement | Why |
|---|---|
| Median runtime | Who is faster |
| Sort time vs union-find time (separate instrumented run) | Where Kruskal's time goes |
| `find` calls and path steps inside `find` | Cost of union-find |
| Number of `union` calls | Should equal V − 1 |
| Heap pushes, stale pops / total pops | Cost of Prim's lazy heap |
| Total MST weight | Correctness — must be identical for both |

## 6. Correctness first (before any timing)

- Both methods return the **same total weight** (edge sets may differ when weights tie).
- Each result has exactly **V − 1 edges** and **connects all vertices**.
- Hand-checked small graphs (4–6 vertices) in `tests/`.
- `networkx` is used **only inside tests** as an independent oracle.

## 7. Plan by milestone

| Sessions | Goal | Deliverable |
|---|---|---|
| **1–3** | Charter | Research question, prediction, Graph ADT contract → [`docs/charter.md`](docs/charter.md) |
| **4–7** | Baselines + checkpoint | Kruskal, Prim, union-find, generators, all tests green · oral checkpoint (design slides + prototype) · protocol frozen |
| **8–10** | Data collection | Pilot run, full benchmark sweep, results in `results/`, first figures |
| **11–13** | Defense | Robustness checks, statistical analysis, final report + presentation |

**Optional extensions** (only if the core is done early): Kruskal *without* path compression;
Prim with an O(V²) array instead of a heap.

## 8. Who does what

| Nurlan | Gunel |
|---|---|
| Graph ADT, graph generators | Prim + heap counters |
| Union-find + Kruskal with counters | Benchmark runner (warm-up, 7 reps, median, caps) |
| Correctness tests | Analysis notebook + figures |
| **Together:** charter, checkpoint slides, interpretation, final defense | |

Both of us must be able to explain **every** part of the code in the individual defense.

## 9. Repository layout

```
src/mst/graph.py        weighted undirected Graph ADT (shared by both methods)
src/mst/generators.py   random graphs (spanning tree first) and grid graphs
src/mst/union_find.py   union by rank + path compression, with counters
src/mst/kruskal.py      Kruskal's algorithm
src/mst/prim.py         Prim's algorithm (heapq, lazy deletion)
src/bench/run.py        benchmark runner -> results/*.csv
tests/                  correctness tests (pytest; networkx oracle)
docs/charter.md         project charter
results/                raw benchmark output
figures/                generated plots
```

## 10. Environment and how to run

- Python **3.12** (record the exact version in the report: `python --version`)
- Measured code uses the **standard library only**; `pandas` and `matplotlib` for analysis.

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
python -m pytest                # correctness first
python -m src.bench.run --quick # smoke test, a few seconds
python -m src.bench.run         # full benchmark -> results/*.csv + environment *.json
```

## 11. Status

- [x] Charter: aim, research questions, refutable hypotheses
- [x] Graph ADT, generators (random, grid, matched), union-find, Kruskal, Prim, with counters
- [x] Tests: hand-checked graphs, `networkx` oracle, edge cases, heavy ties, counter invariants
- [x] Benchmark runner following the timing protocol (smoke-tested)
- [ ] Pilot run on our laptops → adjust sizes if needed → freeze protocol
- [ ] Full sweep, analysis notebook, figures
