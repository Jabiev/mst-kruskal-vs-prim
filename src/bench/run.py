"""Benchmark runner.

Protocol (catalogue rules):
- generate every graph BEFORE timing
- 1 untimed warm-up, then 7 timed repetitions (time.perf_counter), record the median
- 5 s / 256 MiB cap per run; a timeout is written to the results, never dropped
- both methods run on exactly the same graph instances
Output: one CSV row per (family, n, p, seed, method) in results/.
"""


def main():
    raise NotImplementedError


if __name__ == "__main__":
    main()
