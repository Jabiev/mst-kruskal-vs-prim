"""Weighted undirected Graph ADT shared by Kruskal and Prim.

Contract: see docs/charter.md. Vertices are the integers 0..n-1.
"""


class Graph:
    def __init__(self, n):
        # TODO: store n and an adjacency list (one list of (v, w) per vertex)
        raise NotImplementedError

    def add_edge(self, u, v, w):
        """Add the undirected edge u-v with weight w."""
        raise NotImplementedError

    def neighbors(self, u):
        """Return an iterable of (v, w) pairs."""
        raise NotImplementedError

    def edges(self):
        """Return an iterable of (u, v, w), each undirected edge exactly once."""
        raise NotImplementedError

    def num_vertices(self):
        raise NotImplementedError

    def num_edges(self):
        raise NotImplementedError
