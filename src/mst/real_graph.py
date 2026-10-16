"""The real graph (Baku road network, built by scripts/build_real_graph.py) and the
inputs derived from it.

Three ways to use the real data:
- load_edge_list():  the whole road network (11 838 intersections, 15 117 streets).
- road_ball(n, seed): a connected piece of the real road network with n intersections,
  grown by breadth-first search from a seeded start. Same structure, controlled size.
- geo_knn(n, k, seed): n real intersections (seeded sample), each linked to its k nearest
  neighbours by straight-line distance. Real positions, controlled density: k = 4 is
  road-like, larger k is denser, k = n - 1 is the complete graph. Weight = straight-line
  distance in centimetres (cost of a direct link between two sites).
"""

import csv
import math
import random
from collections import deque
from functools import lru_cache
from pathlib import Path

from .graph import Graph

DATA = Path(__file__).resolve().parents[2] / "data"
BAKU_ROADS = DATA / "baku_roads.csv"
BAKU_NODES = DATA / "baku_nodes.csv"
EARTH_RADIUS_M = 6_371_008.8


def load_edge_list(path=BAKU_ROADS):
    """Read a u,v,w CSV (with header) into a Graph. Vertices must be 0..n-1. O(E)."""
    g = Graph(1 + max(max(u, v) for u, v, _ in _edges(path)))
    for u, v, w in _edges(path):
        g.add_edge(u, v, w)
    return g


@lru_cache(maxsize=None)
def _edges(path):
    with open(path, newline="") as f:
        return tuple((int(u), int(v), int(w)) for u, v, w in list(csv.reader(f))[1:])


@lru_cache(maxsize=None)
def load_points(path=BAKU_NODES):
    """Intersection positions as (x, y) in metres (local equirectangular projection)."""
    with open(path, newline="") as f:
        rows = [(float(lat), float(lon)) for _, lat, lon in list(csv.reader(f))[1:]]
    lat0 = math.radians(sum(lat for lat, _ in rows) / len(rows))
    k = math.pi / 180 * EARTH_RADIUS_M
    return tuple((lon * k * math.cos(lat0), lat * k) for lat, lon in rows)


def _relabel(vertices, edges):
    ids = {v: i for i, v in enumerate(sorted(vertices))}
    g = Graph(len(ids))
    for u, v, w in edges:
        g.add_edge(ids[u], ids[v], w)
    return g


def road_ball(n, seed):
    """Connected n-vertex piece of the road network: BFS from a seeded random start,
    then every road between the collected intersections. O(V + E)."""
    edges = _edges(BAKU_ROADS)
    total = 1 + max(max(u, v) for u, v, _ in edges)
    if not 1 <= n <= total:
        raise ValueError(f"n must be in [1, {total}]")
    adj = [[] for _ in range(total)]
    for u, v, _ in edges:
        adj[u].append(v)
        adj[v].append(u)
    start = random.Random(seed).randrange(total)
    picked = {start}
    queue = deque([start])
    while queue and len(picked) < n:
        x = queue.popleft()
        for y in adj[x]:
            if y not in picked and len(picked) < n:
                picked.add(y)
                queue.append(y)
    if len(picked) < n:
        raise ValueError("start vertex's component is smaller than n")
    return _relabel(picked, [(u, v, w) for u, v, w in edges if u in picked and v in picked])


def geo_knn(n, k, seed):
    """n sampled real intersections, each joined to its k nearest neighbours (symmetric:
    an edge exists if either endpoint chose the other). If the result is disconnected,
    the largest connected component is kept, so the returned graph may have fewer than n
    vertices. O(n^2 log n) to build, outside any timed part."""
    pts = load_points()
    if not 2 <= n <= len(pts):
        raise ValueError(f"n must be in [2, {len(pts)}]")
    k = min(k, n - 1)
    sample = random.Random(seed).sample(range(len(pts)), n)
    xy = [pts[i] for i in sample]

    chosen = set()
    for i in range(n):
        xi, yi = xy[i]
        dist = sorted(((xi - xj) ** 2 + (yi - yj) ** 2, j) for j, (xj, yj) in enumerate(xy) if j != i)
        for _, j in dist[:k]:
            chosen.add((min(i, j), max(i, j)))
    edges = [(i, j, max(1, round(100 * math.dist(xy[i], xy[j])))) for i, j in sorted(chosen)]

    # largest connected component
    adj = [[] for _ in range(n)]
    for i, j, _ in edges:
        adj[i].append(j)
        adj[j].append(i)
    seen, best = [False] * n, []
    for s in range(n):
        if seen[s]:
            continue
        comp, stack = [], [s]
        seen[s] = True
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if not seen[y]:
                    seen[y] = True
                    stack.append(y)
        if len(comp) > len(best):
            best = comp
    keep = set(best)
    return _relabel(keep, [e for e in edges if e[0] in keep])
