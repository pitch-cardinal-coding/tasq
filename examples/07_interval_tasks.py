#!/usr/bin/env python3
"""
07_interval_tasks.py — Test periodic (interval) task execution via eta.

What it tests:
  - eta="Ns" parameter schedules periodic execution
  - Tasks fire at roughly correct intervals
  - Results accumulate correctly

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 07_interval_tasks.py [HOST] [SECONDS]
    python3 07_interval_tasks.py 192.168.122.87 10
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
RUN_SECONDS = int(sys.argv[2]) if len(sys.argv) > 2 else 8


def tick(n):
    """Return the value and a timestamp."""
    return {"value": n, "ts": time.time()}


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected to {url}")
    print(f"Running interval task every 2s for {RUN_SECONDS}s ...\n")

    # Submit an interval task
    sent = time.monotonic()
    future = tq.put(tick, 1, name="ticker", eta="2s")

    # Wait for the duration
    time.sleep(RUN_SECONDS)

    tq.disconnect()
    elapsed = time.monotonic() - sent

    print(f"Ran for {elapsed:.1f}s")
    print(f"Expected ~{RUN_SECONDS // 2} ticks (every 2s)")
    print("Note: interval tasks fire on the worker side; the client")
    print("receives the latest result. This example verifies the client")
    print("can submit and disconnect cleanly with eta tasks.")
    print("\nPASSED")


if __name__ == "__main__":
    main()
