"""Correctness before timing. These fail until the implementations exist."""

import networkx as nx
import pytest

from src.mst.generators import grid_graph, random_graph
from src.mst.graph import Graph
from src.mst.kruskal import kruskal
from src.mst.prim import prim


def small_graph():
    # Hand-checked: MST = 0-2 (1), 1-3 (2), 0-3 (3) -> total 6
    g = Graph(4)
    for u, v, w in [(0, 1, 4), (0, 2, 1), (0, 3, 3), (1, 3, 2), (2, 3, 5)]:
        g.add_edge(u, v, w)
    return g


def oracle_weight(g):
    G = nx.Graph()
    G.add_nodes_from(range(g.num_vertices()))
    G.add_weighted_edges_from(g.edges())
    return nx.minimum_spanning_tree(G).size(weight="weight")


def is_spanning_tree(n, edges):
    if len(edges) != n - 1:
        return False
    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from((u, v) for u, v, _ in edges)
    return nx.is_connected(G)


@pytest.mark.parametrize("algo", [kruskal, prim])
def test_hand_checked(algo):
    edges, total, _ = algo(small_graph())
    assert total == 6
    assert is_spanning_tree(4, edges)


@pytest.mark.parametrize("seed", range(5))
@pytest.mark.parametrize("make", [
    lambda s: random_graph(60, 0.1, s),
    lambda s: grid_graph(8, 8, s),
])
def test_matches_oracle(make, seed):
    g = make(seed)
    k_edges, k_total, _ = kruskal(g)
    p_edges, p_total, _ = prim(g)
    assert k_total == p_total == oracle_weight(g)
    assert is_spanning_tree(g.num_vertices(), k_edges)
    assert is_spanning_tree(g.num_vertices(), p_edges)
