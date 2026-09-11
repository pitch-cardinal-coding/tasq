#!/usr/bin/env python3
"""
06_delayed_tasks.py — Test delayed (scheduled) task execution.

What it tests:
  - delay parameter causes execution to wait
  - Multiple delayed tasks run at correct times
  - Mixed immediate and delayed tasks

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 06_delayed_tasks.py [HOST]
    python3 06_delayed_tasks.py 192.168.122.87
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def timestamped_add(a, b, _sent_time=None):
    """Add two numbers and report when the function actually ran."""
    return {
        "result": a + b,
        "ran_at": time.time(),
    }


def immediate_add(a, b):
    return a + b


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected to {url}\n")

    errors = 0

    # Test 1: Delayed task
    print("Test 1: 2-second delayed task ...")
    sent = time.monotonic()
    fut = tq.put(timestamped_add, 10, 20, name="delayed-2s", delay=2)
    result = fut.unwrap()
    elapsed = time.monotonic() - sent
    print(f"  Result: {result['result']}")
    print(f"  Elapsed: {elapsed:.2f}s (expected ~2s)")
    if result["result"] != 30:
        errors += 1
        print("  FAIL: wrong result")
    elif elapsed < 1.5:
        errors += 1
        print("  FAIL: executed too fast, delay not respected")
    else:
        print("  OK")

    # Test 2: Immediate vs delayed
    print("Test 2: Immediate vs delayed comparison ...")
    sent = time.monotonic()
    fut_imm = tq.put(immediate_add, 1, 1, name="immediate")
    fut_del = tq.put(immediate_add, 2, 2, name="delayed-1s", delay=1)
    imm_result = fut_imm.unwrap()
    imm_time = time.monotonic() - sent

    sent_del = time.monotonic()
    del_result = fut_del.unwrap()
    del_time = time.monotonic() - sent_del

    print(f"  Immediate: {imm_result} in {imm_time:.3f}s")
    print(f"  Delayed: {del_result} in {del_time:.3f}s (expected ~1s)")
    if imm_result != 2 or del_result != 4:
        errors += 1
        print("  FAIL: wrong results")
    elif del_time < 0.5:
        errors += 1
        print("  FAIL: delayed task executed too fast")
    else:
        print("  OK")

    # Test 3: Multiple delayed tasks
    print("Test 3: Multiple 1-second delayed tasks ...")
    sent = time.monotonic()
    futs = []
    for i in range(5):
        fut = tq.put(immediate_add, i, i, name=f"multi-delay-{i}", delay=1)
        futs.append(fut)

    results = [f.unwrap() for f in futs]
    elapsed = time.monotonic() - sent
    expected = [0, 2, 4, 6, 8]
    print(f"  Results: {results} (expected {expected})")
    print(f"  Elapsed: {elapsed:.2f}s")
    if results == expected and elapsed >= 0.8:
        print("  OK")
    else:
        errors += 1
        print("  FAIL")

    tq.disconnect()
    print(f"\n{'PASSED' if errors == 0 else f'FAILED ({errors} errors)'}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
