"""Benchmark runner.

Protocol (catalogue rules):
- generate every graph BEFORE timing
- 1 untimed warm-up, then 7 timed repetitions (time.perf_counter), record the median
- 5 s / 256 MiB cap per run; a timeout is written to the results, never dropped
- both methods run on exactly the same graph instances
Output: one CSV row per (family, label, param, seed, method) in results/.

Two experiments:
- main:      Kruskal vs Prim, with where the time goes (sort / union-find / heap)
- unionfind: Kruskal with the four union-find variants (decision 2)

Extra measurements, each in its own run so they never disturb the timed repetitions:
- peak memory: one run under tracemalloc (tracemalloc slows code down, so it is untimed)
- phases: Kruskal sort vs union-find; Prim heap time by replay (see phases.py)
- verification: every result is checked with verify_mst (decision 5)

Caps are checked after each run (Python cannot safely interrupt a running function), so
a run that exceeds 5 s is finished, recorded with status 'timeout', and the remaining
repetitions for that cell are skipped.

Usage:
    python -m src.bench.run                          # main experiment, full sweep
    python -m src.bench.run --experiment unionfind   # union-find variants
    python -m src.bench.run --quick                  # small smoke test
"""

import argparse
import csv
import gc
import json
import platform
import statistics
import sys
import tracemalloc
from datetime import datetime
from functools import partial
from pathlib import Path
from time import perf_counter

from src.bench.phases import kruskal_phases, prim_heap_time
from src.mst.generators import grid_graph, random_graph, random_graph_m
from src.mst.kruskal import kruskal
from src.mst.prim import prim
from src.mst.real_graph import geo_knn, load_edge_list, road_ball
from src.mst.union_find import VARIANTS
from src.mst.verify import verify_mst

TIME_CAP_S = 5.0
MEM_CAP_MIB = 256.0

EXPERIMENTS = {
    "main": {"kruskal": ("both", kruskal), "prim": ("", prim)},
    "unionfind": {
        f"kruskal_{name}": (name, partial(kruskal, by_rank=r, compress=c))
        for name, (r, c) in VARIANTS.items()
    },
}

FIELDS = [
    "experiment", "family", "label", "param", "n_vertices", "n_edges", "density", "seed", "method",
    "uf_variant", "status", "median_s", "min_s", "max_s", "reps", "total_weight",
    "verified", "peak_mib", "find_calls", "path_steps", "unions", "edges_scanned",
    "pushes", "pops", "stale_pops", "sort_s", "union_find_s", "heap_s",
]


def settings(quick):
    """List of (family, label, param, make(seed) -> Graph, seeded). Mirrors docs/charter.md.

    Real data: the whole road network, connected road pieces of controlled size, and
    real intersections linked to their k nearest neighbours (controlled density).
    Controls: random graphs, grids, and random graphs matched to the grids' V and E.
    """
    if quick:
        balls, knn_n, knn_k = [1000], [200], [4, 64]
        sizes, probs, grids = [200], [0.05, 0.2], [(8, 8)]
    else:
        balls, knn_n, knn_k = [1000, 3000, 10000], [200, 500, 1000], [4, 16, 64, 256]
        sizes, probs, grids = [200, 500, 1000], [0.01, 0.05, 0.20], [(32, 32), (64, 64)]
    out = [("road", "baku_full", "", lambda s: load_edge_list(), False)]  # one fixed instance
    for n in balls:
        out.append(("road", f"V={n}", "", lambda s, n=n: road_ball(n, s), True))
    for n in knn_n:
        for k in knn_k:
            if k < n:
                out.append(("geo_knn", f"V={n}", f"k={k}", lambda s, n=n, k=k: geo_knn(n, k, s), True))
    for n in sizes:
        for p in probs:
            out.append(("random", f"V={n}", f"p={p}", lambda s, n=n, p=p: random_graph(n, p, s), True))
    for r, c in grids:
        n, m = r * c, r * (c - 1) + (r - 1) * c
        out.append(("grid", f"{r}x{c}", "", lambda s, r=r, c=c: grid_graph(r, c, s), True))
        # random graph with exactly the grid's V and E, so only structure differs
        out.append(("matched", f"{r}x{c}", "", lambda s, n=n, m=m: random_graph_m(n, m, s), True))
    return out


def time_once(algo, g):
    t0 = perf_counter()
    result = algo(g)
    return perf_counter() - t0, result


def measure(algo, g, reps):
    """Warm-up + memory run + timed reps. Returns (row fields, mst edges, total weight)."""
    row = {}
    warm_s, (edges, total, counters) = time_once(algo, g)  # untimed warm-up (only checks the cap)
    row.update(counters)
    row["total_weight"] = total

    tracemalloc.start()
    algo(g)
    peak = tracemalloc.get_traced_memory()[1] / 2**20
    tracemalloc.stop()
    row["peak_mib"] = round(peak, 3)

    if warm_s > TIME_CAP_S:
        row.update(status="timeout", reps=0)
        return row, edges, total
    if peak > MEM_CAP_MIB:
        row.update(status="memory", reps=0)
        return row, edges, total

    times = []
    gc_was_enabled = gc.isenabled()
    gc.disable()  # same choice as timeit: no collector pauses inside the timed part
    try:
        for _ in range(reps):
            t, _ = time_once(algo, g)
            times.append(t)
            if t > TIME_CAP_S:
                break
    finally:
        if gc_was_enabled:
            gc.enable()

    row.update(
        status="timeout" if times[-1] > TIME_CAP_S else "ok",
        reps=len(times),
        median_s=statistics.median(times),
        min_s=min(times),
        max_s=max(times),
    )
    return row, edges, total


def phases(method, variant, g):
    if method == "prim":
        return {"heap_s": prim_heap_time(g)}
    r, c = VARIANTS[variant]
    p = {}
    kruskal(g, phase_times=p, by_rank=r, compress=c)
    return {"sort_s": p["sort"], "union_find_s": p["union_find"]}


def environment():
    return {
        "python": sys.version,
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "machine": platform.machine(),
        "started": datetime.now().isoformat(timespec="seconds"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--experiment", choices=EXPERIMENTS, default="main")
    ap.add_argument("--quick", action="store_true", help="small smoke-test sweep")
    ap.add_argument("--seeds", type=int, help="seeds per setting (default 10, quick 2)")
    ap.add_argument("--reps", type=int, help="timed repetitions (default 7, quick 3)")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args(argv)

    seeds = args.seeds or (2 if args.quick else 10)
    reps = args.reps or (3 if args.quick else 7)
    methods = EXPERIMENTS[args.experiment]
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = f"{args.experiment}_{'quick' if args.quick else 'full'}_{stamp}"
    csv_path = args.out / f"{tag}.csv"
    env = environment() | {"experiment": args.experiment, "seeds": seeds, "reps": reps,
                           "csv": csv_path.name}
    (args.out / f"{tag}.json").write_text(json.dumps(env, indent=2))

    cells = settings(args.quick)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for i, (family, label, param, make, seeded) in enumerate(cells, 1):
            t_cell = perf_counter()
            for seed in range(seeds if seeded else 1):
                g = make(seed)  # generated outside every timed part
                V, E = g.num_vertices(), g.num_edges()
                base = dict(experiment=args.experiment, family=family, label=label,
                            param=param, n_vertices=V, n_edges=E,
                            density=round(2 * E / (V * (V - 1)), 6),
                            seed=seed if seeded else "")
                # alternate the order so no method always runs first
                order = list(methods) if seed % 2 == 0 else list(reversed(methods))
                totals = {}
                for name in order:
                    variant, algo = methods[name]
                    row, edges, totals[name] = measure(algo, g, reps)
                    row["verified"] = verify_mst(g, edges, totals[name])  # raises if not an MST
                    row.update(phases("prim" if name == "prim" else "kruskal", variant, g))
                    writer.writerow(base | {"method": name, "uf_variant": variant} | row)
                if len(set(totals.values())) != 1:
                    raise RuntimeError(f"MST weights differ on {family} {label} seed {seed}: {totals}")
                f.flush()
            print(f"[{i}/{len(cells)}] {family:8} {label:10} {param:7} "
                  f"E={g.num_edges():>6}  {perf_counter() - t_cell:6.1f} s", flush=True)
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
