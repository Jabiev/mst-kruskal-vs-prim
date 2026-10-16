"""Prim's algorithm with our binary heap and lazy deletion."""

from .binary_heap import BinaryHeap


def prim(graph, start=0, heap=None):
    """Return (mst_edges, total_weight, counters).

    counters: dict with 'pushes', 'pops', 'stale_pops'.
    A pop is stale when its vertex is already in the tree: skip it and count it.

    Lazy deletion: instead of decreasing a key, a new (weight, vertex, parent) entry is
    pushed and old entries are left in the heap; they show up later as stale pops.
    The loop stops as soon as all vertices are in the tree. Raises ValueError if the
    graph is not connected.

    heap: an empty heap object to use (default: a new BinaryHeap). The instrumented run
    passes a RecordingHeap to capture the exact sequence of heap operations.
    """
    n = graph.num_vertices()
    if n == 0:
        return [], 0, {"pushes": 0, "pops": 0, "stale_pops": 0}

    if heap is None:
        heap = BinaryHeap()
    push, pop = heap.push, heap.pop
    in_tree = [False] * n
    in_tree[start] = True
    pushes = pops = stale = 0
    for v, w in graph.neighbors(start):
        push((w, v, start))
        pushes += 1

    mst = []
    total = 0
    while len(heap) and len(mst) < n - 1:
        w, v, u = pop()
        pops += 1
        if in_tree[v]:
            stale += 1
            continue
        in_tree[v] = True
        mst.append((u, v, w))
        total += w
        for x, wx in graph.neighbors(v):
            if not in_tree[x]:
                push((wx, x, v))
                pushes += 1

    if len(mst) != n - 1:
        raise ValueError("graph is not connected: no spanning tree exists")

    return mst, total, {"pushes": pushes, "pops": pops, "stale_pops": stale}
