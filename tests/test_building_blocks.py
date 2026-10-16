"""Tests for our own sort, binary heap, union-find variants and the MST verifier."""

import heapq
import random

import pytest

from src.mst.binary_heap import BinaryHeap, RecordingHeap
from src.mst.generators import grid_graph, random_graph
from src.mst.graph import Graph
from src.mst.kruskal import kruskal
from src.mst.prim import prim
from src.mst.sorting import merge_sort
from src.mst.union_find import VARIANTS, UnionFind
from src.mst.verify import NotAnMST, verify_mst

from .test_correctness import oracle_weight


# ---------- merge sort ----------

@pytest.mark.parametrize("n", [0, 1, 2, 3, 7, 8, 9, 100, 1000])
def test_merge_sort_matches_sorted(n):
    rng = random.Random(n)
    data = [(rng.randint(1, 10), i) for i in range(n)]  # many ties
    key = lambda x: x[0]
    assert merge_sort(data, key) == sorted(data, key=key)  # sorted() is stable too


def test_merge_sort_is_stable_and_does_not_modify_input():
    data = [(3, "a"), (1, "b"), (3, "c"), (1, "d"), (2, "e")]
    copy = list(data)
    assert merge_sort(data, lambda x: x[0]) == [(1, "b"), (1, "d"), (2, "e"), (3, "a"), (3, "c")]
    assert data == copy


def test_merge_sort_already_sorted_and_reversed():
    up = list(range(500))
    assert merge_sort(up, lambda x: x) == up
    assert merge_sort(up[::-1], lambda x: x) == up


# ---------- binary heap ----------

def test_heap_random_operations_match_heapq():
    rng = random.Random(0)
    ours, ref = BinaryHeap(), []
    for _ in range(5000):
        if ref and rng.random() < 0.45:
            assert ours.pop() == heapq.heappop(ref)
        else:
            item = (rng.randint(1, 20), rng.randint(0, 99))
            ours.push(item)
            heapq.heappush(ref, item)
        assert len(ours) == len(ref)
    while ref:
        assert ours.pop() == heapq.heappop(ref)


def test_heap_pop_empty_raises():
    with pytest.raises(IndexError):
        BinaryHeap().pop()


def test_recording_heap_records_and_behaves_the_same():
    h = RecordingHeap()
    for x in [5, 1, 4]:
        h.push(x)
    assert h.pop() == 1
    assert h.trace == [5, 1, 4, None]


# ---------- union-find variants (decision 2) ----------

@pytest.mark.parametrize("variant", VARIANTS)
def test_all_union_find_variants_give_an_mst(variant):
    by_rank, compress = VARIANTS[variant]
    g = random_graph(80, 0.15, 1)
    edges, total, c = kruskal(g, by_rank=by_rank, compress=compress)
    assert total == oracle_weight(g)
    assert verify_mst(g, edges, total)
    assert c["unions"] == 79


def test_optimisations_reduce_path_steps():
    """On a chain built in the worst order, neither optimisation gives long paths."""
    steps = {}
    for name, (by_rank, compress) in VARIANTS.items():
        uf = UnionFind(2000, by_rank=by_rank, compress=compress)
        for i in range(1, 2000):
            uf.union(i, i - 1)  # naive linking puts each new root on top: a long chain
        for i in range(2000):
            uf.find(i)
        steps[name] = uf.path_steps
    assert steps["neither"] > 50 * steps["both"]
    assert steps["rank_only"] < steps["neither"]
    assert steps["compression_only"] < steps["neither"]


def test_without_compression_paths_stay_long():
    uf = UnionFind(3, by_rank=False, compress=False)
    uf.parent = [0, 0, 1]
    uf.find(2)
    assert uf.parent == [0, 0, 1]  # unchanged
    assert uf.path_steps == 2


# ---------- MST verifier (decision 5) ----------

def square():
    # 0-1 (1), 1-2 (1), 2-3 (1), 3-0 (1), 0-2 (5): four equal edges, several MSTs
    g = Graph(4)
    for u, v, w in [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 0, 1), (0, 2, 5)]:
        g.add_edge(u, v, w)
    return g


def test_verifier_accepts_every_tied_mst():
    g = square()
    ring = [(0, 1, 1), (1, 2, 1), (2, 3, 1), (3, 0, 1)]
    for skip in range(4):  # dropping any one of the four equal edges gives an MST
        tree = [e for i, e in enumerate(ring) if i != skip]
        assert verify_mst(g, tree, 3)


@pytest.mark.parametrize("tree, total", [
    ([(0, 1, 1), (1, 2, 1), (0, 2, 5)], 7),  # contains a cycle
    ([(0, 1, 1), (1, 2, 1)], 2),  # too few edges
    ([(0, 1, 1), (0, 2, 5), (2, 3, 1)], 7),  # spanning tree, but not minimum
    ([(0, 1, 1), (1, 2, 1), (1, 3, 1)], 3),  # edge 1-3 is not in the graph
    ([(0, 1, 1), (1, 2, 1), (2, 3, 1)], 99),  # wrong reported total
])
def test_verifier_rejects_wrong_trees(tree, total):
    with pytest.raises(NotAnMST):
        verify_mst(square(), tree, total)


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("make", [
    lambda s: random_graph(120, 0.1, s, w_max=5),
    lambda s: grid_graph(12, 12, s, w_max=5),
])
def test_both_algorithms_pass_the_verifier(make, seed):
    g = make(seed)
    for algo in (kruskal, prim):
        edges, total, _ = algo(g)
        assert verify_mst(g, edges, total)


def test_verifier_catches_a_swapped_edge():
    g = random_graph(60, 0.2, 7)
    edges, total, _ = kruskal(g)
    tree = {(min(u, v), max(u, v)) for u, v, _ in edges}
    # replace the lightest tree edge by the heaviest non-tree edge that keeps a spanning tree
    for u, v, w in sorted(g.edges(), key=lambda e: -e[2]):
        if (min(u, v), max(u, v)) in tree:
            continue
        for i in range(len(edges)):
            candidate = edges[:i] + edges[i + 1:] + [(u, v, w)]
            try:
                verify_mst(g, candidate, sum(x[2] for x in candidate))
            except NotAnMST as e:
                if "lighter than the tree path" in str(e):
                    return  # a valid spanning tree that is not minimum was rejected
    pytest.fail("no non-minimal spanning tree was produced")
