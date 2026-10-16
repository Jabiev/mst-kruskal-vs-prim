"""Where does the time go? Phase measurements, each in a run separate from the timing.

Kruskal: sort vs union-find loop, timed directly with two extra perf_counter calls.

Prim: heap operations are interleaved with the rest of the loop (thousands of short
calls), and timing each call would cost as much as the call itself. Instead:
1. run Prim once with a RecordingHeap, which stores the exact sequence of push/pop
   operations (with their items);
2. replay that sequence on a fresh BinaryHeap and time it;
3. subtract the time of the same replay loop with the heap calls removed (loop overhead).
The result is the time Prim spends inside heap operations; the remainder of Prim's
median runtime is graph traversal and bookkeeping.
"""

from time import perf_counter

from src.mst.binary_heap import BinaryHeap, RecordingHeap
from src.mst.kruskal import kruskal
from src.mst.prim import prim


def kruskal_phases(graph):
    phases = {}
    kruskal(graph, phase_times=phases)
    return {"sort_s": phases["sort"], "union_find_s": phases["union_find"]}


def _replay(trace):
    heap = BinaryHeap()
    push, pop = heap.push, heap.pop
    t0 = perf_counter()
    for item in trace:
        if item is None:
            pop()
        else:
            push(item)
    return perf_counter() - t0


def _replay_overhead(trace):
    def push(item):
        pass

    def pop():
        pass

    t0 = perf_counter()
    for item in trace:
        if item is None:
            pop()
        else:
            push(item)
    return perf_counter() - t0


def prim_heap_time(graph, reps=5):
    """Median time (s) spent inside heap push/pop during one Prim run."""
    rec = RecordingHeap()
    prim(graph, heap=rec)
    trace = rec.trace
    times = sorted(_replay(trace) - _replay_overhead(trace) for _ in range(reps))
    return max(times[len(times) // 2], 0.0)
