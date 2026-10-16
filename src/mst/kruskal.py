"""Kruskal's algorithm: sort all edges, keep an edge unless it closes a cycle."""

from time import perf_counter

from .sorting import merge_sort
from .union_find import UnionFind


def _weight(edge):
    return edge[2]


def kruskal(graph, phase_times=None, by_rank=True, compress=True):
    """Return (mst_edges, total_weight, counters).

    counters: dict with 'find_calls', 'path_steps', 'unions', 'edges_scanned'.
    The sort is part of the algorithm and must stay inside this function (it is timed).

    phase_times: optional dict (decision 3). When given, the time spent sorting and the
    time spent in the union-find loop are written to phase_times['sort'] and
    phase_times['union_find'] (seconds). Only the separate instrumented run passes it;
    the main timed run passes None so the extra timers never affect the reported runtime.

    by_rank, compress: union-find optimisations, switched off only for the ablation
    (decision 2).

    The scan stops as soon as V - 1 edges are accepted (standard early exit); the sort
    of all E edges has already been paid by then. Raises ValueError if the graph is not
    connected.
    """
    n = graph.num_vertices()

    t0 = perf_counter() if phase_times is not None else 0.0
    edges = merge_sort(graph.edges(), _weight)
    if phase_times is not None:
        t1 = perf_counter()
        phase_times["sort"] = t1 - t0

    uf = UnionFind(n, by_rank=by_rank, compress=compress)
    union = uf.union
    mst = []
    total = 0
    scanned = 0
    for u, v, w in edges:
        if len(mst) == n - 1:
            break
        scanned += 1
        if union(u, v):
            mst.append((u, v, w))
            total += w

    if phase_times is not None:
        phase_times["union_find"] = perf_counter() - t1

    if n > 0 and len(mst) != n - 1:
        raise ValueError("graph is not connected: no spanning tree exists")

    counters = {
        "find_calls": uf.find_calls,
        "path_steps": uf.path_steps,
        "unions": uf.unions,
        "edges_scanned": scanned,
    }
    return mst, total, counters
