"""Prim's algorithm with heapq and lazy deletion."""

from heapq import heappop, heappush


def prim(graph, start=0):
    """Return (mst_edges, total_weight, counters).

    counters: dict with 'pushes', 'pops', 'stale_pops'.
    A pop is stale when its vertex is already in the tree: skip it and count it.

    Lazy deletion: instead of decreasing a key, a new (weight, vertex, parent) entry is
    pushed and old entries are left in the heap; they show up later as stale pops.
    The loop stops as soon as all vertices are in the tree. Raises ValueError if the
    graph is not connected.
    """
    n = graph.num_vertices()
    if n == 0:
        return [], 0, {"pushes": 0, "pops": 0, "stale_pops": 0}

    in_tree = [False] * n
    in_tree[start] = True
    heap = []
    pushes = pops = stale = 0
    for v, w in graph.neighbors(start):
        heappush(heap, (w, v, start))
        pushes += 1

    mst = []
    total = 0
    while heap and len(mst) < n - 1:
        w, v, u = heappop(heap)
        pops += 1
        if in_tree[v]:
            stale += 1
            continue
        in_tree[v] = True
        mst.append((u, v, w))
        total += w
        for x, wx in graph.neighbors(v):
            if not in_tree[x]:
                heappush(heap, (wx, x, v))
                pushes += 1

    if len(mst) != n - 1:
        raise ValueError("graph is not connected: no spanning tree exists")

    return mst, total, {"pushes": pushes, "pops": pops, "stale_pops": stale}
