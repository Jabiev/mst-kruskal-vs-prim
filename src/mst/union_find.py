"""Disjoint sets with union by rank and path compression (Cormen et al., ch. 'Data
Structures for Disjoint Sets'). Counters are part of the measurements.

Each optimisation can be switched off (decision 2), giving four variants:
both, rank only, compression only, neither. Every variant runs the same code (the
switches are checked in all of them), so the comparison measures the optimisation,
not a different implementation.
"""

VARIANTS = {
    "both": (True, True),
    "rank_only": (True, False),
    "compression_only": (False, True),
    "neither": (False, False),
}


class UnionFind:
    def __init__(self, n, by_rank=True, compress=True):
        self.parent = list(range(n))
        self.rank = [0] * n
        self.by_rank = by_rank
        self.compress = compress
        self.find_calls = 0
        self.path_steps = 0  # parent links followed inside find
        self.unions = 0

    def find(self, x):
        """Return the representative of x's set (compressing the path if enabled)."""
        self.find_calls += 1
        parent = self.parent
        # First pass: walk up to the root, counting the links followed.
        root = x
        while parent[root] != root:
            root = parent[root]
            self.path_steps += 1
        # Second pass: point every vertex on the path directly at the root.
        if self.compress:
            while parent[x] != root:
                parent[x], x = root, parent[x]
        return root

    def union(self, x, y):
        """Merge the sets of x and y. Return False if they were already together."""
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self.by_rank:
            if self.rank[rx] < self.rank[ry]:
                rx, ry = ry, rx
            if self.rank[rx] == self.rank[ry]:
                self.rank[rx] += 1
        # attach ry under rx: the taller tree's root with by_rank, else simply y's root
        self.parent[ry] = rx
        self.unions += 1
        return True
