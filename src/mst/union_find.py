"""Disjoint sets with union by rank and path compression (Cormen et al., ch. 'Data
Structures for Disjoint Sets'). Counters are part of the measurements."""


class UnionFind:
    def __init__(self, n):
        # TODO: parent, rank
        self.find_calls = 0
        self.path_steps = 0  # parent links followed inside find
        self.unions = 0
        raise NotImplementedError

    def find(self, x):
        """Return the representative of x's set, compressing the path."""
        raise NotImplementedError

    def union(self, x, y):
        """Merge the sets of x and y. Return False if they were already together."""
        raise NotImplementedError
