#!/usr/bin/env python3
"""
02_concurrent_tasks.py — Submit many tasks concurrently, collect all results.

What it tests:
  - Multiple async put() calls without blocking
  - Collecting results from futures in order
  - Correctness under concurrency (results match inputs)

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 02_concurrent_tasks.py [HOST] [COUNT]
    python3 02_concurrent_tasks.py 192.168.122.87 100
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 50


def square(n):
    return n * n


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected, submitting {COUNT} tasks ...")

    start = time.monotonic()

    # Fire all tasks
    futures = []
    for i in range(COUNT):
        fut = tq.put(square, i, name=f"sq-{i}")
        futures.append((i, fut))

    # Collect all results
    results = []
    for i, fut in futures:
        results.append((i, fut.unwrap()))

    elapsed = time.monotonic() - start

    # Verify correctness
    errors = 0
    for i, val in results:
        expected = i * i
        if val != expected:
            print(f"  FAIL: square({i}) = {val}, expected {expected}")
            errors += 1

    throughput = COUNT / elapsed
    print(f"Results: {COUNT - errors}/{COUNT} correct")
    print(f"Total time: {elapsed:.3f}s ({throughput:.0f} tasks/s)")

    tq.disconnect()
    if errors == 0:
        print("PASSED")
    else:
        print(f"FAILED ({errors} errors)")
        sys.exit(1)


if __name__ == "__main__":
    main()
