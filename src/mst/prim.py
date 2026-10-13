"""Prim's algorithm with heapq and lazy deletion."""


def prim(graph, start=0):
    """Return (mst_edges, total_weight, counters).

    counters: dict with 'pushes', 'pops', 'stale_pops'.
    A pop is stale when its vertex is already in the tree: skip it and count it.
    """
    raise NotImplementedError
