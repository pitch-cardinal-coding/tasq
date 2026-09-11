#!/usr/bin/env python3
"""
11_performance_bench.py — Benchmark throughput and latency.

What it tests:
  - Single-task latency
  - Sustained throughput
  - Burst capacity
  - Memory-safe repeated sends

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 11_performance_bench.py [HOST]
    python3 11_performance_bench.py 192.168.122.87
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def noop():
    return True


def add(a, b):
    return a + b


def cpu_work(n):
    """CPU-bound work: sum of squares."""
    return sum(i * i for i in range(n))


def bench(label, func, iterations):
    """Run func() iterations times and report timing."""
    start = time.monotonic()
    for _ in range(iterations):
        func()
    elapsed = time.monotonic() - start
    rate = iterations / elapsed
    print(f"  {label}: {iterations} iterations in {elapsed:.3f}s ({rate:.0f}/s)")
    return elapsed, rate


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected to {url}\n")

    # --- Benchmark 1: Single-task latency ---
    print("Benchmark 1: Single-task latency (10 measurements) ...")
    latencies = []
    for i in range(10):
        start = time.monotonic()
        tq.put(noop, name=f"lat-{i}").unwrap()
        latencies.append(time.monotonic() - start)

    avg_lat = sum(latencies) / len(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    print(f"  avg: {avg_lat * 1000:.1f}ms  min: {min_lat * 1000:.1f}ms  max: {max_lat * 1000:.1f}ms")

    # --- Benchmark 2: Throughput ---
    print("\nBenchmark 2: Throughput (200 noop tasks) ...")
    start = time.monotonic()
    futures = [tq.put(noop, name=f"tp-{i}") for i in range(200)]
    for f in futures:
        f.unwrap()
    elapsed = time.monotonic() - start
    print(f"  200 tasks in {elapsed:.3f}s ({200 / elapsed:.0f} tasks/s)")

    # --- Benchmark 3: Burst send then collect ---
    print("\nBenchmark 3: Burst pattern (fire 100, then collect) ...")
    start = time.monotonic()
    futs = [tq.put(add, i, i, name=f"burst-{i}") for i in range(100)]
    fire_time = time.monotonic() - start
    print(f"  Fire phase: {fire_time:.3f}s")

    start = time.monotonic()
    results = [f.unwrap() for f in futs]
    collect_time = time.monotonic() - start
    print(f"  Collect phase: {collect_time:.3f}s")
    print(f"  Total: {fire_time + collect_time:.3f}s")

    # Verify
    assert results == [i * 2 for i in range(100)]

    # --- Benchmark 4: CPU-bound throughput ---
    print("\nBenchmark 4: CPU-bound (20 tasks, sum of 100K squares) ...")
    start = time.monotonic()
    futs = [tq.put(cpu_work, 100_000, name=f"cpu-{i}") for i in range(20)]
    results = [f.unwrap() for f in futs]
    elapsed = time.monotonic() - start
    print(f"  20 tasks in {elapsed:.3f}s ({20 / elapsed:.1f} tasks/s)")

    # Verify one result
    expected = sum(i * i for i in range(100_000))
    assert results[0] == expected

    # --- Benchmark 5: Memory safety (sustained load) ---
    print("\nBenchmark 5: Memory safety (500 rapid tasks) ...")
    start = time.monotonic()
    for i in range(500):
        tq.put(add, i, 1, name=f"mem-{i}").unwrap()
    elapsed = time.monotonic() - start
    print(f"  500 tasks in {elapsed:.3f}s ({500 / elapsed:.0f} tasks/s)")

    tq.disconnect()
    print("\nPASSED")


if __name__ == "__main__":
    main()
