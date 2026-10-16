# Kruskal vs Prim — Where Does the Time Go?

**Project Work 1 · T05 Minimum spanning trees** — M1 Data Science and Artificial
Intelligence · UFAZ · Advanced Data Structures and Algorithms · Fall 2026

Team: Nurlan Jabiyev · Gunel Rzayeva

---

## Research question

> How do edge density and graph structure, in synthetic and real-life graphs, affect the
> runtime of Kruskal's and Prim's algorithms, and how much do union-find and heap
> operations contribute?

Both algorithms return a tree of the same total weight, so we compare **cost, not result**.
Big-O does not decide the winner: Kruskal is O(E log E), heap-Prim is O(E log V), and since
E ≤ V², **both are Θ(E log V)**. Constant factors decide, and only measurement shows them.

Full plan, hypotheses, decisions and definitions: [`docs/charter.md`](docs/charter.md).

## The real graph: Baku road network

| | |
|---|---|
| Source | OpenStreetMap (Overpass API), central Baku, © OpenStreetMap contributors, ODbL |
| Size | 11 838 intersections, 15 117 street segments (average degree 2.55) |
| Weight | street length in centimetres |
| MST meaning | shortest street length along which a cable connects every intersection: 875.19 km of 1 532.92 km |

Roads have real weights (Twitter and Wikipedia graphs do not), and the MST has a real
meaning (cable layout). From the same data we derive inputs of controlled **size**
(connected road pieces) and controlled **density** (real intersections linked to their k
nearest neighbours). Random graphs and grids serve as controls.

## What we implemented

| Component | File | Complexity |
|---|---|---|
| Graph (adjacency list + edge list) | `src/mst/graph.py` | O(1) add edge |
| Merge sort (bottom-up, stable) | `src/mst/sorting.py` | O(E log E) |
| Binary heap | `src/mst/binary_heap.py` | O(log n) push / pop |
| Union-find (rank, compression, each switchable) | `src/mst/union_find.py` | O(α(n)) amortised |
| Kruskal | `src/mst/kruskal.py` | O(E log E) |
| Prim (lazy deletion) | `src/mst/prim.py` | O(E log V) |
| MST proof check (cycle property) | `src/mst/verify.py` | O((V + E) log V) |
| Generators: random, grid, matched, road pieces, k-nearest | `src/mst/generators.py`, `src/mst/real_graph.py` | outside timing |
| Phase measurement (sort / union-find / heap) | `src/bench/phases.py` | separate runs |
| Benchmark runner | `src/bench/run.py` | — |

## Experiments

| Experiment | Compares | Command |
|---|---|---|
| `main` | Kruskal vs Prim on every family; sort, union-find and heap time | `python -m src.bench.run` |
| `unionfind` | Kruskal with both / rank only / compression only / neither | `python -m src.bench.run --experiment unionfind` |

Protocol: graphs built before timing · same instance for both methods · 1 warm-up ·
7 timed repetitions · median · 5 s / 256 MiB caps, timeouts kept · 10 seeds · every result
verified as an MST.

## How to run

Python 3.12 (CPython from python.org).

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate                  # Windows
pip install -r requirements.txt
python -m pytest                        # correctness first
python -m src.bench.run --quick         # smoke test
python -m src.bench.run                 # main experiment   -> results/*.csv + *.json
python -m src.bench.run --experiment unionfind
python scripts/build_real_graph.py      # optional: rebuild data/ from OpenStreetMap
```

## Repository layout

```
src/mst/          graph, sorting, binary heap, union-find, Kruskal, Prim, verifier, generators
src/bench/        benchmark runner and phase measurements
scripts/          real graph download and conversion
data/             Baku road network (edges, intersection positions, provenance)
tests/            correctness tests (pytest; networkx used only here)
docs/charter.md   research question, hypotheses, decisions, protocol
results/          benchmark output
figures/          plots
```

## Status

- [x] Charter: research question, real graph, hypotheses, decisions 1–5, protocol
- [x] All components implemented, 111 tests passing
- [x] Real graph built and verified
- [ ] Pilot run → time budget → freeze protocol (checkpoint)
- [ ] Main runs, statistical analysis, figures
- [ ] Checkpoint and defence slides
