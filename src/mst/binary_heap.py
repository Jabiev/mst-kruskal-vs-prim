"""Array-based binary min-heap used by Prim (lazy deletion: no decrease-key).

Items are compared with <, so Prim stores (weight, vertex, parent) tuples.
Both operations use the "hole" technique: the moving item is written once at its final
position instead of being swapped at every level.
"""


class BinaryHeap:
    __slots__ = ("_a",)

    def __init__(self):
        self._a = []

    def __len__(self):
        return len(self._a)

    def push(self, item):
        """Add item. O(log n)."""
        a = self._a
        a.append(item)
        i = len(a) - 1
        while i > 0:
            p = (i - 1) >> 1
            if item < a[p]:
                a[i] = a[p]  # move the parent down into the hole
                i = p
            else:
                break
        a[i] = item

    def pop(self):
        """Remove and return the smallest item. O(log n). IndexError if empty."""
        a = self._a
        last = a.pop()
        if not a:
            return last
        top = a[0]
        n = len(a)
        i = 0
        while True:
            c = 2 * i + 1
            if c >= n:
                break
            if c + 1 < n and a[c + 1] < a[c]:
                c += 1
            if a[c] < last:
                a[i] = a[c]  # move the smaller child up into the hole
                i = c
            else:
                break
        a[i] = last
        return top


class RecordingHeap(BinaryHeap):
    """BinaryHeap that also records every operation, for the heap-time replay (RQ2).

    trace entries: the pushed item for a push, None for a pop.
    Only the separate instrumented run uses it; timed runs use BinaryHeap.
    """

    __slots__ = ("trace",)

    def __init__(self):
        super().__init__()
        self.trace = []

    def push(self, item):
        self.trace.append(item)
        BinaryHeap.push(self, item)

    def pop(self):
        self.trace.append(None)
        return BinaryHeap.pop(self)
