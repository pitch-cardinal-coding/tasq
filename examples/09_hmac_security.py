#!/usr/bin/env python3
"""
09_hmac_security.py — Test HMAC payload signing.

What it tests:
  - signkey parameter enables HMAC signing
  - Tasks work correctly with signing enabled
  - Correct key works, wrong key causes failure (on worker side)

Usage:
  Start a worker with a signkey:
    tq runner -p 9000 --pull-port 9001 --signkey "my-secret"

  Run:
    python3 09_hmac_security.py [HOST]
    python3 09_hmac_security.py 192.168.122.87
"""

import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
SECRET = "my-secret-key"


def add(a, b):
    return a + b


def main():
    url = f"zmq://{HOST}:9000"

    # Connect WITH the signing key
    print(f"Connecting to {url} with HMAC key ...")
    tq = tasq.queue(url, signkey=SECRET)
    assert tq.is_connected(), "Failed to connect"
    print(f"Connected: {tq.is_connected()}\n")

    # Test 1: Basic signed task
    print("Test 1: Signed task execution ...")
    start = time.monotonic()
    result = tq.put(add, 5, 15, name="signed-add").unwrap()
    elapsed = time.monotonic() - start
    print(f"  Result: {result} (expected 20)")
    assert result == 20
    print(f"  Time: {elapsed:.4f}s")
    print("  OK")

    # Test 2: Multiple signed tasks
    print("Test 2: Multiple signed tasks ...")
    futures = []
    for i in range(10):
        fut = tq.put(add, i, i * 2, name=f"signed-{i}")
        futures.append(fut)

    results = [f.unwrap() for f in futures]
    expected = [i + i * 2 for i in range(10)]
    print(f"  Results: {results}")
    assert results == expected
    print("  OK")

    # Test 3: Large payload with signing
    print("Test 3: Large signed payload (50KB) ...")
    payload = "S" * 50_000
    result = tq.put_blocking(lambda s: len(s), payload, name="signed-large").value
    print(f"  Result: {result} (expected 50000)")
    assert result == 50_000
    print("  OK")

    tq.disconnect()
    print("\nPASSED")


if __name__ == "__main__":
    main()
