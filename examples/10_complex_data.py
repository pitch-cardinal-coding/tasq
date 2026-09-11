#!/usr/bin/env python3
"""
10_complex_data.py — Test complex data structure serialization.

What it tests:
  - Nested dicts and lists
  - Custom classes (via cloudpickle)
  - Closures and lambdas
  - Mixed types (int, float, str, None, bool)
  - Deeply nested structures

Usage:
  Start a worker first:
    tq runner -p 9000 --pull-port 9001

  Run:
    python3 10_complex_data.py [HOST]
    python3 10_complex_data.py 192.168.122.87
"""

import sys

import tasq

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"


def echo(x):
    return x


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance_to(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __repr__(self):
        return f"Point({self.x}, {self.y})"


def make_point(x, y):
    return Point(x, y)


def process_points(points):
    """Calculate total distance through a list of points."""
    total = 0
    for i in range(len(points) - 1):
        total += points[i].distance_to(points[i + 1])
    return round(total, 4)


def main():
    url = f"zmq://{HOST}:9000"
    tq = tasq.queue(url)
    print(f"Connected to {url}\n")

    errors = 0

    # Test 1: Nested dict
    print("Test 1: Nested dict ...")
    data = {"a": {"b": {"c": [1, 2, 3]}}}
    result = tq.put_blocking(echo, data, name="nest-dict").value
    if result == data:
        print("  OK")
    else:
        errors += 1
        print(f"  FAIL: {result}")

    # Test 2: Custom class
    print("Test 2: Custom class (Point) ...")
    p1 = tq.put_blocking(make_point, 3, 4, name="point-1").value
    p2 = tq.put_blocking(make_point, 0, 0, name="point-2").value
    dist = tq.put_blocking(process_points, [p1, p2], name="dist").value
    expected_dist = 5.0
    print(f"  Distance: {dist} (expected {expected_dist})")
    if dist == expected_dist:
        print("  OK")
    else:
        errors += 1
        print("  FAIL")

    # Test 3: Mixed types
    print("Test 3: Mixed types ...")
    data = {
        "int": 42,
        "float": 3.14159,
        "str": "hello",
        "none": None,
        "bool_true": True,
        "bool_false": False,
        "list": [1, "two", 3.0, None],
        "nested": {"key": [True, False, None]},
    }
    result = tq.put_blocking(echo, data, name="mixed").value
    if result == data:
        print("  OK")
    else:
        errors += 1
        print(f"  FAIL: {result}")

    # Test 4: Deeply nested
    print("Test 4: Deeply nested (10 levels) ...")
    data = {"level": 0}
    current = data
    for i in range(1, 10):
        current["next"] = {"level": i}
        current = current["next"]
    result = tq.put_blocking(echo, data, name="deep").value
    if result == data:
        print("  OK")
    else:
        errors += 1
        print("  FAIL")

    # Test 5: Large nested list
    print("Test 5: 5000-element nested list ...")
    data = [[i, str(i), {"v": i * 0.1}] for i in range(5000)]
    result = tq.put_blocking(echo, data, name="big-nest").value
    if result == data:
        print("  OK")
    else:
        errors += 1
        print("  FAIL")

    # Test 6: Closure
    print("Test 6: Closure ...")
    multiplier = 7

    def multiply_by_fixed(x):
        return x * multiplier

    result = tq.put_blocking(multiply_by_fixed, 6, name="closure").value
    print(f"  Result: {result} (expected 42)")
    if result == 42:
        print("  OK")
    else:
        errors += 1
        print("  FAIL")

    # Test 7: Tuple return
    print("Test 7: Tuple return ...")

    def return_tuple():
        return (1, "two", 3.0)

    result = tq.put_blocking(return_tuple, name="tuple").value
    expected = (1, "two", 3.0)
    if result == expected:
        print("  OK")
    else:
        errors += 1
        print(f"  FAIL: {result}")

    tq.disconnect()
    print(f"\n{'PASSED' if errors == 0 else f'FAILED ({errors} errors)'}")
    if errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
