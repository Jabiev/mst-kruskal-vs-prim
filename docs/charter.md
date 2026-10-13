# Project Charter — T05: Kruskal vs Prim

_Draft for sessions 1–3. Fill in the blanks together, then freeze it._

## Team
- Nurlan Jabiyev
- _partner_

## Research question
How do edge density and graph structure affect the runtime of Kruskal's and Prim's
algorithms, and how much do union-find and heap operations contribute?

## Application
Designing the cheapest network that connects all sites — cables, pipelines, roads —
and a building block of clustering.

## Prediction
- Kruskal is faster on sparse graphs.
- Prim overtakes Kruskal as density grows, because Kruskal must sort every edge.
- Union-find overhead stays small (path steps per `find` close to 1).
- On grid graphs (always sparse) Kruskal wins at every size.

## Graph ADT contract
| Operation | Meaning | Expected cost |
|---|---|---|
| `Graph(n)` | empty graph with vertices `0..n-1` | O(n) |
| `add_edge(u, v, w)` | undirected edge with integer weight `w` | O(1) |
| `neighbors(u)` | iterable of `(v, w)` pairs | O(deg u) |
| `edges()` | iterable of `(u, v, w)`, each edge once | O(E) |
| `num_vertices()`, `num_edges()` | sizes | O(1) |

## Methods
- **Kruskal:** sort edges + union-find (union by rank, path compression).
- **Prim:** `heapq` with lazy deletion (stale entries skipped and counted).

## Experimental design
- Random graphs: V = 200, 500, 1000; p = 0.01, 0.05, 0.20; weights 1..100; spanning tree first.
- Grid graphs: 32×32 and 64×64, random weights.
- 10 seeds per setting.
- Timing: 1 untimed warm-up, 7 timed repetitions, median; 5 s and 256 MiB caps.
- Sizes may be adjusted for our laptops: _write any change and the reason here_.

## Measurements
Median runtime · `find` calls and path steps · unions · heap pushes · stale pops / total pops ·
total MST weight.

## Correctness check
Same total weight for both · V − 1 edges · all vertices connected · hand-checked small graphs ·
`networkx` as oracle in tests only.

## Environment
- Python version: _fill in_
- OS / laptop: _fill in_

## Risks
| Risk | Plan |
|---|---|
| Tied weights give different edge sets | Compare total weights, not edge sets |
| Sorting accidentally left outside timing | Sort inside `kruskal()` |
| Runs exceed 5 s | Record as timeout, keep in results |
