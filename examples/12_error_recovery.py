#!/usr/bin/env python3
"""
12_error_recovery.py — Test client behavior around errors and edge cases.

What it tests:
  - Client continues working after worker exception
  - Pending jobs are sent on connect
  - Reconnection after disconnect
  - Double disconnect is safe
  - Large burst of mixed success/error tasks

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 12_error_recovery.py [HOST]
    python3 12_error_recovery.py 192.168.122.87
"""

import sys
import time

import tasq
from tasq.queue import TasqQueue
from tasq.remote.client import Client
from tasq.remote.connection import ZMQBackendConnection

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def add(a, b):
    return a + b


def fail():
    raise ValueError("intentional error")


def main():
    url = f"zmq://{HOST}:9000"
    errors = 0

    # Test 1: Recovery after error
    print("Test 1: Recovery after error ...")
    tq = tasq.queue(url)
    tq.put(fail, name="err1").unwrap()
    result = tq.put(add, 10, 20, name="after-err").unwrap()
    if result == 30:
        print("  OK")
    else:
        errors += 1
        print(f"  FAIL: expected 30, got {result}")
    tq.disconnect()

    # Test 2: Pending jobs on connect
    print("Test 2: Pending jobs flush on connect ...")
    from tasq.remote.connection import ZMQBackendConnection

    conn = ZMQBackendConnection.from_url(url)
    client = Client(conn)

    # Schedule BEFORE connect
    r1 = client.schedule(add, 1, 2, name="pending-1")
    r2 = client.schedule(add, 3, 4, name="pending-2")
    assert r1 is None, "Should return None when not connected"
    assert r2 is None, "Should return None when not connected"

    # Now connect — pending jobs should be sent
    client.connect()
    time.sleep(0.5)  # Let gatherer collect

    # Results should be available
    res1 = client._results.get("pending-1")
    res2 = client._results.get("pending-2")
    if res1 and res1.done() and res1.unwrap() == 3:
        print("  OK (pending-1)")
    else:
        errors += 1
        print(f"  FAIL: pending-1 = {res1}")
    if res2 and res2.done() and res2.unwrap() == 7:
        print("  OK (pending-2)")
    else:
        errors += 1
        print(f"  FAIL: pending-2 = {res2}")
    client.disconnect()

    # Test 3: Double disconnect is safe
    print("Test 3: Double disconnect ...")
    tq3 = tasq.queue(url)
    tq3.disconnect()
    try:
        tq3.disconnect()
        print("  OK (no crash)")
    except Exception as e:
        errors += 1
        print(f"  FAIL: exception on double disconnect: {e}")

    # Test 4: Rapid connect/disconnect cycles
    print("Test 4: Rapid connect/disconnect cycles ...")
    for i in range(5):
        tq_cycle = tasq.queue(url)
        tq_cycle.put(add, i, i, name=f"cycle-{i}").unwrap()
        tq_cycle.disconnect()
    print("  OK (5 cycles)")

    # Test 5: Mixed burst
    print("Test 5: 100 mixed success/error tasks ...")
    tq_mixed = tasq.queue(url)
    ok_count = 0
    err_count = 0
    futures = []
    for i in range(100):
        if i % 3 == 0:
            fut = tq_mixed.put(fail, name=f"mixed-err-{i}")
        else:
            fut = tq_mixed.put(add, i, 1, name=f"mixed-ok-{i}")
        futures.append((i, fut))

    for i, fut in futures:
        result = fut.unwrap()
        if i % 3 == 0:
            if issubclass(result, ValueError):
                err_count += 1
            else:
                errors += 1
                print(f"  FAIL task {i}: expected ValueError, got {result}")
        else:
            if result == i + 1:
                ok_count += 1
            else:
                errors += 1
                print(f"  FAIL task {i}: expected {i + 1}, got {result}")

    print(f"  OK: {ok_count} success, {err_count} errors")
    if ok_count != 66 or err_count != 34:
        errors += 1
        print("  FAIL: wrong counts")

    tq_mixed.disconnect()

    # Test 6: Worker info
    print("Test 6: Queue info ...")
    tq_info = tasq.queue(url)
    connected = tq_info.is_connected()
    pending = len(tq_info)
    tq_info.disconnect()
    print(f"  Connected: {connected}, Pending: {pending}")
    if connected:
        print("  OK")
    else:
        errors += 1
        print("  FAIL")

    print(f"\n{'PASSED' if errors == 0 else f'FAILED ({errors} errors)'}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
