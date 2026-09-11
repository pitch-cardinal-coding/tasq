#!/usr/bin/env python3
"""
08_multiple_workers.py — Connect to multiple workers with multi_queue.

What it tests:
  - tasq.multi_queue() with multiple worker backends
  - Round-robin routing across workers
  - All workers receive tasks and return results
  - Correctness under distribution

Usage:
  Start multiple workers on different ports:
    tq runner -p 9000 --pull-port 9001 &
    tq runner -p 9010 --pull-port 9011 &
    tq runner -p 9020 --pull-port 9021 &

  Run:
    python3 08_multiple_workers.py [HOST] [COUNT]
    python3 08_multiple_workers.py 192.168.122.87 30
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
COUNT = int(sys.argv[2]) if len(sys.argv) > 2 else 30


def multiply(a, b):
    return a * b


def main():
    # Connect to 3 workers
    urls = [
        f"zmq://{HOST}:9000",
        f"zmq://{HOST}:9010",
        f"zmq://{HOST}:9020",
    ]
    print(f"Connecting to {len(urls)} workers ...")

    try:
        mq = tasq.multi_queue(urls)
    except Exception as e:
        print(f"Failed to connect to workers: {e}")
        print("Make sure all workers are running on the specified ports.")
        sys.exit(1)

    print(f"Connected: {mq.is_connected()}")

    # Submit tasks
    print(f"Submitting {COUNT} tasks across workers ...")
    start = time.monotonic()

    futures = []
    for i in range(COUNT):
        fut = mq.put(multiply, i, 3, name=f"multi-{i}")
        futures.append((i, fut))

    results = []
    for i, fut in futures:
        results.append((i, fut.unwrap()))

    elapsed = time.monotonic() - start

    # Verify
    errors = 0
    for i, val in results:
        expected = i * 3
        if val != expected:
            print(f"  FAIL: multiply({i}, 3) = {val}, expected {expected}")
            errors += 1

    throughput = COUNT / elapsed
    print(f"Results: {COUNT - errors}/{COUNT} correct")
    print(f"Time: {elapsed:.3f}s ({throughput:.0f} tasks/s)")

    mq.disconnect()
    print(f"\n{'PASSED' if errors == 0 else f'FAILED ({errors} errors)'}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
