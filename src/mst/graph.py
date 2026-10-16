"""Weighted undirected Graph ADT shared by Kruskal and Prim.

Contract: see docs/charter.md. Vertices are the integers 0..n-1.

Both representations are kept: an adjacency list (what Prim needs) and a flat edge
list (what Kruskal needs). Building both happens once, outside the timed part, so
neither algorithm gets a representation advantage.
"""


class Graph:
    def __init__(self, n):
        if n < 0:
            raise ValueError("number of vertices must be >= 0")
        self._n = n
        self._adj = [[] for _ in range(n)]  # adj[u] = list of (v, w)
        self._edges = []  # each undirected edge once, as (u, v, w)

    def add_edge(self, u, v, w):
        """Add the undirected edge u-v with weight w."""
        if not (0 <= u < self._n and 0 <= v < self._n):
            raise ValueError(f"edge ({u}, {v}) has a vertex outside 0..{self._n - 1}")
        if u == v:
            raise ValueError(f"self-loop at vertex {u} is not allowed")
        self._adj[u].append((v, w))
        self._adj[v].append((u, w))
        self._edges.append((u, v, w))

    def neighbors(self, u):
        """Return an iterable of (v, w) pairs."""
        return self._adj[u]

    def edges(self):
        """Return an iterable of (u, v, w), each undirected edge exactly once."""
        return self._edges

    def num_vertices(self):
        return self._n

    def num_edges(self):
        return len(self._edges)
