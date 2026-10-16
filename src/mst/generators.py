"""Graph generators. Every generator takes a seed so experiments are reproducible.

Each generator uses its own random.Random(seed), never the global random module, so
the same (parameters, seed) always gives exactly the same graph.
"""

import random

from .graph import Graph


def _spanning_tree(n, rng, w_min, w_max):
    """Random spanning tree: shuffle the vertices, join each one to a random earlier one.

    Returns the graph and the set of tree pairs (min, max) so callers can avoid duplicates.
    """
    g = Graph(n)
    order = list(range(n))
    rng.shuffle(order)
    used = set()
    for i in range(1, n):
        u, v = order[i], order[rng.randrange(i)]
        g.add_edge(u, v, rng.randint(w_min, w_max))
        used.add((min(u, v), max(u, v)))
    return g, used


def random_graph(n, p, seed, w_min=1, w_max=100):
    """Connected random graph.

    1. Build a random spanning tree first (guarantees connectivity).
    2. Add every other pair (u, v) with probability p.
    Weights are uniform integers in [w_min, w_max].
    Expected edges: (n - 1) + p * (n(n-1)/2 - (n - 1)).
    """
    rng = random.Random(seed)
    g, used = _spanning_tree(n, rng, w_min, w_max)
    for u in range(n):
        for v in range(u + 1, n):
            if (u, v) not in used and rng.random() < p:
                g.add_edge(u, v, rng.randint(w_min, w_max))
    return g


def random_graph_m(n, m, seed, w_min=1, w_max=100):
    """Connected random graph with exactly m edges (RQ3: matched to a grid's V and E).

    Spanning tree first, then m - (n - 1) distinct extra pairs chosen uniformly.
    """
    max_m = n * (n - 1) // 2
    if not (n - 1 <= m <= max_m):
        raise ValueError(f"m must be in [{n - 1}, {max_m}] for n = {n}")
    rng = random.Random(seed)
    g, used = _spanning_tree(n, rng, w_min, w_max)
    while g.num_edges() < m:
        u, v = rng.randrange(n), rng.randrange(n)
        if u == v:
            continue
        pair = (min(u, v), max(u, v))
        if pair in used:
            continue
        used.add(pair)
        g.add_edge(pair[0], pair[1], rng.randint(w_min, w_max))
    return g


def grid_graph(rows, cols, seed, w_min=1, w_max=100):
    """rows x cols grid; each cell is joined to its right and lower neighbour.

    Vertex (r, c) has id r * cols + c. Edges: rows*(cols-1) + (rows-1)*cols.
    """
    rng = random.Random(seed)
    g = Graph(rows * cols)
    for r in range(rows):
        for c in range(cols):
            u = r * cols + c
            if c + 1 < cols:
                g.add_edge(u, u + 1, rng.randint(w_min, w_max))
            if r + 1 < rows:
                g.add_edge(u, u + cols, rng.randint(w_min, w_max))
    return g
