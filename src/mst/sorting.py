"""Bottom-up merge sort, used by Kruskal to sort edges by weight.

Why merge sort (see docs/charter.md, decision 1):
- O(E log E) in every case: no bad inputs, unlike quicksort, whose two-way partition
  degrades badly on the many equal weights our graphs have (weights 1..100).
- Stable: equal weights keep their input order, so ties are broken the same way on
  every run and the resulting tree is reproducible.
- Bottom-up (iterative): no recursion, so no recursion limit on large edge lists.
- Independent of the binary heap, so Kruskal's sort cost and Prim's heap cost are
  measured on separate code.

Keys are computed once and merged in a parallel list, so each comparison is a plain
number comparison instead of a key-function call.
"""


def merge_sort(items, key):
    """Return a new list with items sorted by key(item), stable."""
    vals = list(items)
    n = len(vals)
    if n < 2:
        return vals
    src_k = [key(x) for x in vals]
    src_v = vals
    dst_k = [None] * n
    dst_v = [None] * n

    width = 1
    while width < n:
        for lo in range(0, n, 2 * width):
            mid = min(lo + width, n)
            hi = min(lo + 2 * width, n)
            i, j, t = lo, mid, lo
            while i < mid and j < hi:
                if src_k[j] < src_k[i]:  # strictly smaller: the left run wins ties (stable)
                    dst_k[t] = src_k[j]
                    dst_v[t] = src_v[j]
                    j += 1
                else:
                    dst_k[t] = src_k[i]
                    dst_v[t] = src_v[i]
                    i += 1
                t += 1
            if i < mid:  # copy whichever run is left over
                dst_k[t:hi] = src_k[i:mid]
                dst_v[t:hi] = src_v[i:mid]
            else:
                dst_k[t:hi] = src_k[j:hi]
                dst_v[t:hi] = src_v[j:hi]
        src_k, dst_k = dst_k, src_k
        src_v, dst_v = dst_v, src_v
        width *= 2
    return src_v
