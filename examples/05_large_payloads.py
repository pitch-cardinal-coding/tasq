#!/usr/bin/env python3
"""
05_large_payloads.py — Test serialization of large data payloads.

What it tests:
  - Sending large strings (100KB, 1MB)
  - Sending large binary data
  - Sending large lists/dicts
  - Round-trip integrity of serialized data
  - Performance under load

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 05_large_payloads.py [HOST]
    python3 05_large_payloads.py 192.168.122.87
"""

import os
import sys
import time

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def echo(data):
    return data


def len_of(data):
    return len(data)


def checksum(data):
    return sum(data) % 256 if isinstance(data, (list, bytes)) else len(str(data))


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected to {url}\n")

    errors = 0

    # Test 1: 100KB string
    print("Test 1: 100KB string ...")
    payload = "A" * 100_000
    start = time.monotonic()
    result = tq.put_blocking(echo, payload, name="str-100k").value
    elapsed = time.monotonic() - start
    if result == payload:
        print(f"  OK (100KB round-trip in {elapsed:.3f}s)")
    else:
        errors += 1
        print(f"  FAIL: length mismatch {len(result)} != {len(payload)}")

    # Test 2: 1MB string
    print("Test 2: 1MB string ...")
    payload = "B" * 1_000_000
    start = time.monotonic()
    result = tq.put_blocking(echo, payload, name="str-1m").value
    elapsed = time.monotonic() - start
    if result == payload:
        print(f"  OK (1MB round-trip in {elapsed:.3f}s)")
    else:
        errors += 1
        print(f"  FAIL: length mismatch {len(result)} != {len(payload)}")

    # Test 3: Large binary data
    print("Test 3: 256KB binary ...")
    payload = os.urandom(256_000)
    result = tq.put_blocking(echo, payload, name="bin-256k").value
    if result == payload:
        print("  OK (256KB binary round-trip)")
    else:
        errors += 1
        print("  FAIL: binary data mismatch")

    # Test 4: Large list
    print("Test 4: 100K element list ...")
    payload = list(range(100_000))
    result = tq.put_blocking(echo, payload, name="list-100k").value
    if result == payload:
        print("  OK (100K list round-trip)")
    else:
        errors += 1
        print("  FAIL: list mismatch")

    # Test 5: Large dict
    print("Test 5: 10K entry dict ...")
    payload = {f"key_{i}": i * 3.14 for i in range(10_000)}
    result = tq.put_blocking(echo, payload, name="dict-10k").value
    if result == payload:
        print("  OK (10K dict round-trip)")
    else:
        errors += 1
        print("  FAIL: dict mismatch")

    # Test 6: Nested structure
    print("Test 6: Nested structure ...")
    payload = {
        "users": [{"id": i, "name": f"user_{i}", "scores": list(range(10))} for i in range(1000)]
    }
    result = tq.put_blocking(echo, payload, name="nested").value
    if result == payload:
        print("  OK (nested structure round-trip)")
    else:
        errors += 1
        print("  FAIL: nested structure mismatch")

    # Test 7: Throughput test
    print("Test 7: Throughput (10x 1MB sends) ...")
    payload = "X" * 1_000_000
    start = time.monotonic()
    for i in range(10):
        tq.put_blocking(echo, payload, name=f"tp-{i}")
    elapsed = time.monotonic() - start
    mb_sent = 10 * 1
    print(f"  {mb_sent / elapsed:.1f} MB/s ({elapsed:.3f}s for {mb_sent}MB)")

    tq.disconnect()
    print(f"\n{'PASSED' if errors == 0 else f'FAILED ({errors} errors)'}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
