#!/usr/bin/env python3
"""
03_blocking_vs_async.py — Compare blocking and async task submission.

What it tests:
  - put() (async, returns future immediately)
  - put_blocking() (blocks until result is ready)
  - Timing difference between the two modes
  - Both modes return correct results

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 03_blocking_vs_async.py [HOST]
    python3 03_blocking_vs_async.py 192.168.122.87
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def heavy_computation(n):
    """Simulate work by computing sum of squares."""
    return sum(i * i for i in range(n))


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected to {url}\n")

    # --- Async mode ---
    N = 20
    print(f"--- Async mode: {N} tasks ---")
    start = time.monotonic()
    futures = []
    for i in range(N):
        fut = tq.put(heavy_computation, 10000, name=f"async-{i}")
        futures.append(fut)

    # Unblock call returns immediately
    put_done = time.monotonic()
    print(f"  put() calls returned in: {put_done - start:.4f}s")

    # Now collect results
    async_results = [f.unwrap() for f in futures]
    async_done = time.monotonic()
    print(f"  All results collected in: {async_done - start:.4f}s")
    print(f"  Correct: {all(r == sum(i * i for i in range(10000)) for r in async_results)}\n")

    # --- Blocking mode ---
    print(f"--- Blocking mode: {N} tasks ---")
    start = time.monotonic()
    blocking_results = []
    for i in range(N):
        res = tq.put_blocking(heavy_computation, 10000, name=f"block-{i}")
        blocking_results.append(res.value)

    blocking_done = time.monotonic()
    print(f"  Total time: {blocking_done - start:.4f}s")
    expected = sum(i * i for i in range(10000))
    print(f"  Correct: {all(r == expected for r in blocking_results)}\n")

    # --- Summary ---
    print("Summary:")
    print(f"  Async throughput:  {N / (async_done - start):.1f} tasks/s")
    print(f"  Blocking throughput: {N / (blocking_done - start):.1f} tasks/s")

    tq.disconnect()
    print("\nPASSED")


if __name__ == "__main__":
    main()
