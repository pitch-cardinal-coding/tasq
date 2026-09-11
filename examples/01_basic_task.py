#!/usr/bin/env python3
"""
01_basic_task.py — Simplest possible tasq usage.

What it tests:
  - Connecting to a remote worker
  - Submitting a single task with arguments
  - Receiving the result via unwrap()
  - Clean disconnect

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 01_basic_task.py [HOST]
    python3 01_basic_task.py 192.168.122.87
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def add(a, b):
    """Trivial function to execute remotely."""
    return a + b


def main():
    url = f"zmq://{HOST}:9000"
    print(f"Connecting to {url} ...")
    tq = tasq.queue(url)
    assert tq.is_connected(), "Failed to connect"
    print(f"Connected: {tq.is_connected()}")

    # Submit a single task
    print("Submitting: add(3, 7) ...")
    start = time.monotonic()
    future = tq.put(add, 3, 7, name="basic-add")
    result = future.unwrap()
    elapsed = time.monotonic() - start

    print(f"Result: {result}")
    print(f"Time: {elapsed:.4f}s")
    assert result == 10, f"Expected 10, got {result}"

    tq.disconnect()
    print("PASSED")


if __name__ == "__main__":
    main()
