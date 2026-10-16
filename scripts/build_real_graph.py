"""Build the real graph: the road network of central Baku from OpenStreetMap.

Decision 4: how the real graph becomes a valid MST input, and what the weights mean.

Meaning: vertices are road intersections and dead ends; an edge is a street segment
between two of them; its weight is the segment's length in centimetres. The MST is then
the shortest set of streets along which a cable (fibre, power) could connect every
intersection.

Conversion steps:
1. Download the drivable streets (OSM "highway" types below) inside BBOX.
2. Undirected: one-way tags are ignored; a cable can be laid in both directions.
3. Keep only intersections and dead ends as vertices; the shape points between them are
   merged into one edge whose weight is the summed great-circle (haversine) length.
4. Remove self-loops (a street returning to the same intersection can never be in an MST).
5. Parallel edges between the same two vertices: keep only the shortest (a longer
   parallel edge can never be in an MST).
6. Keep the largest connected component (cutting at the bounding box leaves a few small
   fragments; an MST needs a connected graph).
7. Relabel vertices 0..n-1 in OSM-id order (deterministic) and round weights to whole
   centimetres, so totals are exact integers and Kruskal and Prim can be compared with ==.

Usage:  python scripts/build_real_graph.py          (downloads once into data/raw/)
Output: data/baku_roads.csv (u,v,w_cm), data/baku_nodes.csv (id,lat,lon) and
data/baku_roads.json (provenance).
Map data (c) OpenStreetMap contributors, ODbL.
"""

import csv
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "baku_osm.json"
OUT_CSV = ROOT / "data" / "baku_roads.csv"
OUT_META = ROOT / "data" / "baku_roads.json"
OUT_NODES = ROOT / "data" / "baku_nodes.csv"

BBOX = (40.35, 49.78, 40.44, 49.97)  # south, west, north, east (central Baku)
HIGHWAYS = [
    "motorway", "trunk", "primary", "secondary", "tertiary", "unclassified",
    "residential", "living_street", "motorway_link", "trunk_link", "primary_link",
    "secondary_link", "tertiary_link",
]
QUERY = (
    f'[out:json][timeout:180];way["highway"~"^({"|".join(HIGHWAYS)})$"]'
    f"({','.join(map(str, BBOX))});(._;>;);out body;"
)
URL = "https://overpass-api.de/api/interpreter"


def download():
    RAW.parent.mkdir(parents=True, exist_ok=True)
    data = urllib.parse.urlencode({"data": QUERY}).encode()
    req = urllib.request.Request(URL, data=data, headers={"User-Agent": "mst-kruskal-vs-prim/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r:
        RAW.write_bytes(r.read())


def haversine_m(a, b):
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6_371_008.8 * math.asin(math.sqrt(h))  # mean Earth radius in metres


def build(osm):
    coords, ways = {}, []
    for el in osm["elements"]:
        if el["type"] == "node":
            coords[el["id"]] = (el["lat"], el["lon"])
        elif el["type"] == "way":
            ways.append(el["nodes"])

    # 3. a node is a vertex if it ends a way or is used more than once (an intersection)
    uses = {}
    for nodes in ways:
        for n in nodes:
            uses[n] = uses.get(n, 0) + 1
    is_vertex = set(n for n, k in uses.items() if k > 1)
    for nodes in ways:
        is_vertex.add(nodes[0])
        is_vertex.add(nodes[-1])

    best = {}  # (a, b) with a < b  ->  shortest length in metres
    stats = {"ways": len(ways), "osm_nodes": len(coords), "self_loops": 0, "parallel": 0}
    for nodes in ways:
        start, length = nodes[0], 0.0
        for prev, cur in zip(nodes, nodes[1:]):
            length += haversine_m(coords[prev], coords[cur])
            if cur in is_vertex:
                if cur == start:
                    stats["self_loops"] += 1  # 4.
                else:
                    key = (min(start, cur), max(start, cur))
                    if key in best:
                        stats["parallel"] += 1  # 5.
                        best[key] = min(best[key], length)
                    else:
                        best[key] = length
                start, length = cur, 0.0

    # 6. largest connected component
    adj = {}
    for a, b in best:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    seen, largest, components = set(), [], 0
    for s in adj:
        if s in seen:
            continue
        components += 1
        comp, stack = [], [s]
        seen.add(s)
        while stack:
            x = stack.pop()
            comp.append(x)
            for y in adj[x]:
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        if len(comp) > len(largest):
            largest = comp
    stats["components"] = components
    keep = set(largest)

    # 7. relabel and round
    ids = {osm_id: i for i, osm_id in enumerate(sorted(keep))}
    edges = sorted(
        (ids[a], ids[b], max(1, round(m * 100)))
        for (a, b), m in best.items() if a in keep
    )
    stats["vertices"] = len(ids)
    stats["edges"] = len(edges)
    stats["dropped_vertices"] = len(adj) - len(ids)
    nodes = [(ids[i], *coords[i]) for i in sorted(keep)]
    return edges, nodes, stats


def main():
    if not RAW.exists():
        print("downloading from OpenStreetMap (Overpass API)...", flush=True)
        download()
    osm = json.loads(RAW.read_text(encoding="utf-8"))
    edges, nodes, stats = build(osm)

    with OUT_CSV.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["u", "v", "w_cm"])
        w.writerows(edges)
    with OUT_NODES.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id", "lat", "lon"])
        w.writerows(nodes)
    meta = {
        "name": "Baku road network (central)",
        "source": "OpenStreetMap via Overpass API",
        "license": "ODbL, (c) OpenStreetMap contributors",
        "osm_timestamp": osm.get("osm3s", {}).get("timestamp_osm_base"),
        "bbox_south_west_north_east": BBOX,
        "highway_types": HIGHWAYS,
        "weight": "street segment length in centimetres (haversine, rounded)",
        **stats,
        "average_degree": round(2 * stats["edges"] / stats["vertices"], 3),
    }
    OUT_META.write_text(json.dumps(meta, indent=2) + "\n")
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    sys.exit(main())
