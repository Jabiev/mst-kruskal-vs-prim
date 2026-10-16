"""Disjoint sets with union by rank and path compression (Cormen et al., ch. 'Data
Structures for Disjoint Sets'). Counters are part of the measurements."""


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.find_calls = 0
        self.path_steps = 0  # parent links followed inside find
        self.unions = 0

    def find(self, x):
        """Return the representative of x's set, compressing the path."""
        self.find_calls += 1
        parent = self.parent
        # First pass: walk up to the root, counting the links followed.
        root = x
        while parent[root] != root:
            root = parent[root]
            self.path_steps += 1
        # Second pass: point every vertex on the path directly at the root.
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(self, x, y):
        """Merge the sets of x and y. Return False if they were already together."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.rank[rx] < self.rank[ry]:
            rx, ry = ry, rx
        self.parent[ry] = rx  # attach the shorter tree under the taller one
        if self.rank[rx] == self.rank[ry]:
            self.rank[rx] += 1
        self.unions += 1
        return True
