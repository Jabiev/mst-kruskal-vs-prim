"""The real graph and the inputs derived from it are valid MST inputs."""

import json
from pathlib import Path

import networkx as nx
import pytest

from src.mst.kruskal import kruskal
from src.mst.prim import prim
from src.mst.real_graph import BAKU_ROADS, geo_knn, load_edge_list, road_ball
from src.mst.verify import verify_mst

from .test_correctness import oracle_weight

META = json.loads((Path(BAKU_ROADS).with_suffix(".json")).read_text())


def as_nx(g):
    G = nx.MultiGraph()
    G.add_nodes_from(range(g.num_vertices()))
    G.add_edges_from((u, v) for u, v, _ in g.edges())
    return G


def test_full_road_network_matches_provenance_and_is_valid():
    g = load_edge_list()
    assert (g.num_vertices(), g.num_edges()) == (META["vertices"], META["edges"])
    assert nx.is_connected(as_nx(g))
    pairs = [(min(u, v), max(u, v)) for u, v, _ in g.edges()]
    assert len(pairs) == len(set(pairs))  # parallel streets merged
    assert all(u != v for u, v in pairs)  # no self-loops
    assert all(isinstance(w, int) and w > 0 for _, _, w in g.edges())


def test_full_road_network_mst():
    g = load_edge_list()
    k_edges, k_total, _ = kruskal(g)
    p_edges, p_total, _ = prim(g)
    assert k_total == p_total == oracle_weight(g)
    assert verify_mst(g, k_edges, k_total)
    assert verify_mst(g, p_edges, p_total)


@pytest.mark.parametrize("seed", range(3))
def test_road_ball(seed):
    g = road_ball(500, seed)
    assert g.num_vertices() == 500
    assert nx.is_connected(as_nx(g))
    assert [*road_ball(500, seed).edges()] == [*g.edges()]  # reproducible
    for algo in (kruskal, prim):
        edges, total, _ = algo(g)
        assert verify_mst(g, edges, total)


@pytest.mark.parametrize("seed", range(3))
@pytest.mark.parametrize("k", [4, 16, 199])
def test_geo_knn(k, seed):
    g = geo_knn(200, k, seed)
    V, E = g.num_vertices(), g.num_edges()
    assert V <= 200 and nx.is_connected(as_nx(g))
    assert [*geo_knn(200, k, seed).edges()] == [*g.edges()]  # reproducible
    if k == 199:
        assert E == V * (V - 1) // 2  # complete graph
    else:
        assert E >= V * k // 2 * 0.9  # roughly k neighbours each
    expected = oracle_weight(g)
    for algo in (kruskal, prim):
        edges, total, _ = algo(g)
        assert total == expected
        assert verify_mst(g, edges, total)


def test_density_grows_with_k():
    sizes = [geo_knn(300, k, 0).num_edges() for k in (4, 16, 64)]
    assert sizes == sorted(sizes) and sizes[0] < sizes[-1] / 5
