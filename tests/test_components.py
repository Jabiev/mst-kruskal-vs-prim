"""Unit tests for the building blocks, edge cases, and counter invariants."""

import networkx as nx
import pytest

from src.mst.generators import grid_graph, random_graph, random_graph_m
from src.mst.graph import Graph
from src.mst.kruskal import kruskal
from src.mst.prim import prim
from src.mst.union_find import UnionFind

from .test_correctness import is_spanning_tree, oracle_weight

ALGOS = [kruskal, prim]


# ---------- Graph ADT ----------

def test_graph_contract():
    g = Graph(3)
    g.add_edge(0, 1, 5)
    g.add_edge(1, 2, 7)
    assert g.num_vertices() == 3
    assert g.num_edges() == 2
    assert sorted(g.edges()) == [(0, 1, 5), (1, 2, 7)]
    assert sorted(g.neighbors(1)) == [(0, 5), (2, 7)]  # undirected: both directions
    assert list(g.neighbors(0)) == [(1, 5)]


@pytest.mark.parametrize("u, v", [(0, 0), (-1, 1), (0, 3)])
def test_graph_rejects_bad_edges(u, v):
    with pytest.raises(ValueError):
        Graph(3).add_edge(u, v, 1)


# ---------- Union-find ----------

def test_union_find_basic():
    uf = UnionFind(5)
    assert uf.union(0, 1) is True
    assert uf.union(1, 0) is False  # already together
    assert uf.union(2, 3) is True
    assert uf.find(0) == uf.find(1)
    assert uf.find(0) != uf.find(2)
    assert uf.union(1, 3) is True
    assert len({uf.find(x) for x in range(4)}) == 1
    assert uf.find(4) == 4
    assert uf.unions == 3


def test_path_compression_flattens():
    uf = UnionFind(4)
    uf.parent = [0, 0, 1, 2]  # hand-made chain 3 -> 2 -> 1 -> 0
    assert uf.find(3) == 0
    assert uf.path_steps == 3
    assert uf.parent == [0, 0, 0, 0]  # every vertex on the path now points at the root
    uf.find(3)
    assert uf.path_steps == 4  # second find needs only one step


# ---------- Generators ----------

@pytest.mark.parametrize("make", [
    lambda s: random_graph(40, 0.2, s),
    lambda s: random_graph_m(40, 100, s),
    lambda s: grid_graph(5, 7, s),
])
def test_generators_reproducible_and_valid(make):
    g1, g2, g3 = make(1), make(1), make(2)
    assert list(g1.edges()) == list(g2.edges())  # same seed, same graph
    assert list(g1.edges()) != list(g3.edges())  # different seed, different graph
    pairs = [(min(u, v), max(u, v)) for u, v, _ in g1.edges()]
    assert len(pairs) == len(set(pairs))  # no duplicate edges
    assert all(1 <= w <= 100 for _, _, w in g1.edges())
    G = nx.Graph(pairs)
    G.add_nodes_from(range(g1.num_vertices()))
    assert nx.is_connected(G)


def test_random_graph_density_extremes():
    assert random_graph(30, 0.0, 0).num_edges() == 29  # spanning tree only
    assert random_graph(30, 1.0, 0).num_edges() == 30 * 29 // 2  # complete


def test_grid_and_matched_sizes():
    g = grid_graph(4, 6, 0)
    assert g.num_vertices() == 24
    assert g.num_edges() == 4 * 5 + 3 * 6
    m = random_graph_m(24, g.num_edges(), 0)
    assert (m.num_vertices(), m.num_edges()) == (24, 38)
    with pytest.raises(ValueError):
        random_graph_m(5, 3, 0)  # fewer than n - 1 edges cannot be connected


# ---------- Algorithms: edge cases ----------

@pytest.mark.parametrize("algo", ALGOS)
def test_single_vertex(algo):
    edges, total, _ = algo(Graph(1))
    assert edges == [] and total == 0


@pytest.mark.parametrize("algo", ALGOS)
def test_two_vertices_parallel_edges(algo):
    g = Graph(2)
    g.add_edge(0, 1, 9)
    g.add_edge(0, 1, 4)  # multigraph: the cheaper copy must win
    edges, total, _ = algo(g)
    assert total == 4 and len(edges) == 1


@pytest.mark.parametrize("algo", ALGOS)
def test_disconnected_raises(algo):
    g = Graph(4)
    g.add_edge(0, 1, 1)
    g.add_edge(2, 3, 1)
    with pytest.raises(ValueError):
        algo(g)


@pytest.mark.parametrize("algo", ALGOS)
def test_all_equal_weights(algo):
    g = random_graph(30, 0.3, 0, w_min=7, w_max=7)
    edges, total, _ = algo(g)
    assert total == 7 * 29
    assert is_spanning_tree(30, edges)


# ---------- Algorithms: against the oracle on harder inputs ----------

@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("make", [
    lambda s: random_graph(50, 0.3, s, w_max=3),  # heavy ties
    lambda s: random_graph(40, 1.0, s),  # complete graph
    lambda s: random_graph(80, 0.0, s),  # tree: MST is the graph itself
    lambda s: random_graph_m(64, 112, s),  # matched to an 8x8 grid
])
def test_hard_inputs_match_oracle(make, seed):
    g = make(seed)
    expected = oracle_weight(g)
    for algo in ALGOS:
        edges, total, _ = algo(g)
        assert total == expected
        assert is_spanning_tree(g.num_vertices(), edges)
        assert sum(w for _, _, w in edges) == total  # reported total matches the edges


def test_prim_start_vertex_does_not_matter():
    g = random_graph(50, 0.2, 3)
    totals = {prim(g, start=s)[1] for s in (0, 17, 49)}
    assert len(totals) == 1


# ---------- Counter invariants (the measurements must be trustworthy) ----------

@pytest.mark.parametrize("seed", range(3))
def test_kruskal_counters(seed):
    g = random_graph(100, 0.1, seed)
    _, _, c = kruskal(g)
    assert c["unions"] == g.num_vertices() - 1
    assert c["find_calls"] == 2 * c["edges_scanned"]  # union() calls find twice
    assert c["edges_scanned"] <= g.num_edges()
    assert c["path_steps"] >= 0


@pytest.mark.parametrize("seed", range(3))
def test_prim_counters(seed):
    g = random_graph(100, 0.1, seed)
    _, _, c = prim(g)
    assert c["pops"] == (g.num_vertices() - 1) + c["stale_pops"]  # each good pop adds a vertex
    assert c["pops"] <= c["pushes"] <= 2 * g.num_edges()


def test_kruskal_phase_times_do_not_change_result():
    g = random_graph(100, 0.1, 0)
    phases = {}
    plain = kruskal(g)
    timed = kruskal(g, phase_times=phases)
    assert plain == timed
    assert set(phases) == {"sort", "union_find"}
    assert all(t >= 0 for t in phases.values())
