"""Graph generators. Every generator takes a seed so experiments are reproducible."""


def random_graph(n, p, seed, w_min=1, w_max=100):
    """Connected random graph.

    1. Build a random spanning tree first (guarantees connectivity).
    2. Add every other pair (u, v) with probability p.
    Weights are uniform integers in [w_min, w_max].
    """
    # TODO: use random.Random(seed), never the global random module
    raise NotImplementedError


def grid_graph(rows, cols, seed, w_min=1, w_max=100):
    """rows x cols grid; each cell is joined to its right and lower neighbour."""
    raise NotImplementedError
