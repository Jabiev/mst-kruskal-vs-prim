"""Benchmark runner.

Protocol (catalogue rules):
- generate every graph BEFORE timing
- 1 untimed warm-up, then 7 timed repetitions (time.perf_counter), record the median
- 5 s / 256 MiB cap per run; a timeout is written to the results, never dropped
- both methods run on exactly the same graph instances
Output: one CSV row per (family, n, p, seed, method) in results/.

Extra measurements, each in its own run so they never disturb the timed repetitions:
- peak memory: one run under tracemalloc (tracemalloc slows code down, so it is untimed)
- Kruskal phase times (RQ2): one run with phase_times, sort vs union-find

Caps are checked after each run (Python cannot safely interrupt a running function), so
a run that exceeds 5 s is finished, recorded with status 'timeout', and the remaining
repetitions for that cell are skipped.

Usage:
    python -m src.bench.run            # full sweep (charter design)
    python -m src.bench.run --quick    # small smoke test, a few seconds
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
from pathlib import Path
from time import perf_counter

from src.mst.generators import grid_graph, random_graph, random_graph_m
from src.mst.kruskal import kruskal
from src.mst.prim import prim

TIME_CAP_S = 5.0
MEM_CAP_MIB = 256.0
METHODS = {"kruskal": kruskal, "prim": prim}

FIELDS = [
    "family", "label", "n_vertices", "n_edges", "p", "seed", "method", "status",
    "median_s", "min_s", "max_s", "reps", "total_weight", "peak_mib",
    "find_calls", "path_steps", "unions", "edges_scanned",
    "pushes", "pops", "stale_pops", "sort_s", "union_find_s",
]


def settings(quick):
    """List of (family, label, p, make(seed) -> Graph). Mirrors docs/charter.md."""
    if quick:
        sizes, probs, grids = [100, 200], [0.05, 0.2], [(8, 8)]
    else:
        sizes, probs, grids = [200, 500, 1000], [0.01, 0.05, 0.20], [(32, 32), (64, 64)]
    out = []
    for n in sizes:
        for p in probs:
            out.append(("random", f"V={n}", p, lambda s, n=n, p=p: random_graph(n, p, s)))
    for r, c in grids:
        n, m = r * c, r * (c - 1) + (r - 1) * c
        out.append(("grid", f"{r}x{c}", "", lambda s, r=r, c=c: grid_graph(r, c, s)))
        # RQ3: random graph with exactly the grid's V and E, so only structure differs
        out.append(("matched", f"{r}x{c}", "", lambda s, n=n, m=m: random_graph_m(n, m, s)))
    return out


def time_once(algo, g):
    t0 = perf_counter()
    result = algo(g)
    return perf_counter() - t0, result


def measure(algo, g, reps):
    """Warm-up + memory run + timed reps. Returns (row fields, total weight)."""
    row = {}
    warm_s, (_, total, counters) = time_once(algo, g)  # untimed warm-up (only checks the cap)
    row.update(counters)
    row["total_weight"] = total

    tracemalloc.start()
    algo(g)
    peak = tracemalloc.get_traced_memory()[1] / 2**20
    tracemalloc.stop()
    row["peak_mib"] = round(peak, 3)

    if warm_s > TIME_CAP_S:
        row.update(status="timeout", reps=0)
        return row, total
    if peak > MEM_CAP_MIB:
        row.update(status="memory", reps=0)
        return row, total

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
    return row, total


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
    ap.add_argument("--quick", action="store_true", help="small smoke-test sweep")
    ap.add_argument("--seeds", type=int, help="seeds per setting (default 10, quick 2)")
    ap.add_argument("--reps", type=int, help="timed repetitions (default 7, quick 3)")
    ap.add_argument("--out", type=Path, default=Path("results"))
    args = ap.parse_args(argv)

    seeds = args.seeds or (2 if args.quick else 10)
    reps = args.reps or (3 if args.quick else 7)
    args.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    tag = "quick" if args.quick else "full"
    csv_path = args.out / f"bench_{tag}_{stamp}.csv"
    env = environment() | {"seeds": seeds, "reps": reps, "csv": csv_path.name}
    (args.out / f"bench_{tag}_{stamp}.json").write_text(json.dumps(env, indent=2))

    cells = settings(args.quick)
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for i, (family, label, p, make) in enumerate(cells, 1):
            for seed in range(seeds):
                g = make(seed)  # generated outside every timed part
                base = dict(family=family, label=label, n_vertices=g.num_vertices(),
                            n_edges=g.num_edges(), p=p, seed=seed)
                # alternate the order so neither method always runs first
                order = list(METHODS) if seed % 2 == 0 else list(reversed(METHODS))
                totals = {}
                for name in order:
                    row, totals[name] = measure(METHODS[name], g, reps)
                    if name == "kruskal":
                        phases = {}
                        kruskal(g, phase_times=phases)  # separate instrumented run (RQ2)
                        row.update(sort_s=phases["sort"], union_find_s=phases["union_find"])
                    writer.writerow(base | {"method": name} | row)
                if len(set(totals.values())) != 1:
                    raise RuntimeError(f"MST weights differ on {family} {label} seed {seed}: {totals}")
                f.flush()
            print(f"[{i}/{len(cells)}] {family:8} {label:7} p={p!s:5} "
                  f"E~{g.num_edges():>6}  done", flush=True)
    print(f"wrote {csv_path}")


if __name__ == "__main__":
    main()
