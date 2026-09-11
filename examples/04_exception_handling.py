#!/usr/bin/env python3
"""
04_exception_handling.py — Verify exceptions propagate from workers to clients.

What it tests:
  - Exception raised in remote function is captured
  - Correct exception type is preserved
  - Client continues working after an error
  - Mixed success/failure tasks interleave correctly

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 04_exception_handling.py [HOST]
    python3 04_exception_handling.py 192.168.122.87
"""

import sys

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def risky_divide(a, b):
    return a / b


def risky_index(lst, idx):
    return lst[idx]


def add(a, b):
    return a + b


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected to {url}\n")

    errors = 0

    # Test 1: Division by zero
    print("Test 1: Division by zero ...")
    fut = tq.put(risky_divide, 10, 0, name="div-zero")
    result = fut.unwrap()
    is_zero_div = issubclass(result, ZeroDivisionError)
    print(f"  Exception type: {result.__name__ if is_zero_div else result}")
    if not is_zero_div:
        errors += 1
        print("  FAIL: expected ZeroDivisionError")
    else:
        print("  OK")

    # Test 2: Index out of range
    print("Test 2: Index out of range ...")
    fut = tq.put(risky_index, [1, 2, 3], 99, name="idx-oob")
    result = fut.unwrap()
    is_idx_err = issubclass(result, IndexError)
    print(f"  Exception type: {result.__name__ if is_idx_err else result}")
    if not is_idx_err:
        errors += 1
        print("  FAIL: expected IndexError")
    else:
        print("  OK")

    # Test 3: Custom exception
    print("Test 3: Custom exception ...")

    def custom_error():
        raise RuntimeError("custom failure")

    fut = tq.put(custom_error, name="custom-err")
    result = fut.unwrap()
    is_runtime = issubclass(result, RuntimeError)
    print(f"  Exception type: {result.__name__ if is_runtime else result}")
    if not is_runtime:
        errors += 1
        print("  FAIL: expected RuntimeError")
    else:
        print("  OK")

    # Test 4: Successful task after errors
    print("Test 4: Success after errors ...")
    fut = tq.put(add, 100, 200, name="after-err")
    result = fut.unwrap()
    if result == 300:
        print(f"  OK (result={result})")
    else:
        errors += 1
        print(f"  FAIL: expected 300, got {result}")

    # Test 5: Interleaved success/error
    print("Test 5: Interleaved tasks ...")
    futs_ok = [tq.put(add, i, i, name=f"int-ok-{i}") for i in range(5)]
    futs_err = [tq.put(risky_divide, 1, 0, name=f"int-err-{i}") for i in range(5)]

    ok_vals = [f.unwrap() for f in futs_ok]
    err_vals = [f.unwrap() for f in futs_err]

    ok_correct = ok_vals == [0, 2, 4, 6, 8]
    err_correct = all(issubclass(e, ZeroDivisionError) for e in err_vals)
    print(f"  Success results: {ok_vals} {'OK' if ok_correct else 'FAIL'}")
    print(f"  Error results: {[e.__name__ for e in err_vals]} {'OK' if err_correct else 'FAIL'}")
    if not ok_correct or not err_correct:
        errors += 1

    tq.disconnect()
    print(f"\n{'PASSED' if errors == 0 else f'FAILED ({errors} errors)'}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
