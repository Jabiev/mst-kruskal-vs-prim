"""Independent proof that a result is a minimum spanning tree (decision 5).

Equal weights allow several different MSTs, so comparing edge sets is wrong and
comparing only total weights needs a trusted reference. Instead we check the
definition directly, with no external library:

1. it is a spanning tree: V - 1 edges, no cycle (hence connected);
2. every tree edge really exists in the graph with that weight;
3. the reported total equals the sum of the tree's weights;
4. cycle property: for every graph edge (u, v, w), the heaviest edge on the tree path
   from u to v weighs at most w. A spanning tree is minimum if and only if this holds,
   whatever tie-breaking was used.

Path maxima are found with binary lifting: O((V + E) log V).
"""

from collections import Counter, deque


class NotAnMST(AssertionError):
    pass


def verify_mst(graph, tree_edges, total):
    """Raise NotAnMST with a reason if tree_edges is not an MST of graph; else return True."""
    n = graph.num_vertices()
    if n == 0:
        if tree_edges or total != 0:
            raise NotAnMST("empty graph must give an empty tree")
        return True

    # 1. spanning tree: n - 1 edges and no cycle
    if len(tree_edges) != n - 1:
        raise NotAnMST(f"{len(tree_edges)} edges, expected {n - 1}")
    parent = list(range(n))

    def root(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, v, _ in tree_edges:
        ru, rv = root(u), root(v)
        if ru == rv:
            raise NotAnMST(f"edge ({u}, {v}) closes a cycle")
        parent[ru] = rv

    # 2. every tree edge exists in the graph (as a multiset, so each copy is used once)
    available = Counter((min(u, v), max(u, v), w) for u, v, w in graph.edges())
    for u, v, w in tree_edges:
        key = (min(u, v), max(u, v), w)
        if available[key] == 0:
            raise NotAnMST(f"edge ({u}, {v}, {w}) is not in the graph")
        available[key] -= 1

    # 3. reported total
    if sum(w for _, _, w in tree_edges) != total:
        raise NotAnMST("reported total does not match the tree's weights")

    # 4. cycle property, via binary lifting on the tree rooted at 0
    adj = [[] for _ in range(n)]
    for u, v, w in tree_edges:
        adj[u].append((v, w))
        adj[v].append((u, w))
    depth = [0] * n
    up = [0] * n  # parent
    up_w = [0] * n  # weight of the edge to the parent
    seen = [False] * n
    seen[0] = True
    queue = deque([0])
    while queue:
        x = queue.popleft()
        for y, w in adj[x]:
            if not seen[y]:
                seen[y] = True
                depth[y] = depth[x] + 1
                up[y] = x
                up_w[y] = w
                queue.append(y)

    levels = max(1, (n - 1).bit_length())
    anc = [up]
    mx = [up_w]
    for k in range(1, levels):
        a_prev, m_prev = anc[-1], mx[-1]
        anc.append([a_prev[a_prev[x]] for x in range(n)])
        mx.append([max(m_prev[x], m_prev[a_prev[x]]) for x in range(n)])

    def path_max(u, v):
        best = float("-inf")
        if depth[u] < depth[v]:
            u, v = v, u
        diff = depth[u] - depth[v]
        k = 0
        while diff:
            if diff & 1:
                best = max(best, mx[k][u])
                u = anc[k][u]
            diff >>= 1
            k += 1
        if u == v:
            return best
        for k in range(levels - 1, -1, -1):
            if anc[k][u] != anc[k][v]:
                best = max(best, mx[k][u], mx[k][v])
                u, v = anc[k][u], anc[k][v]
        return max(best, up_w[u], up_w[v])

    for u, v, w in graph.edges():
        if path_max(u, v) > w:
            raise NotAnMST(f"edge ({u}, {v}, {w}) is lighter than the tree path between them")
    return True
