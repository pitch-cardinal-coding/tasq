# Tasq Examples

Runnable examples demonstrating every feature of the Tasq distributed task
queue. Each example is self-contained, named numerically by complexity, and
includes its own docstring explaining what it tests.

## Prerequisites

```sh
pip install -e /path/to/tasq
```

## Quick Start

### 1. Start a worker (any machine on the network)

```sh
# Default: actor workers on localhost:9000/9001
tq --log-level DEBUG

# Bind to all interfaces (required for remote access)
tq -a 0.0.0.0 -p 9000 --pull-port 9001 --log-level DEBUG

# Or use the helper script
python3 examples/server.py 0.0.0.0 9000

# Process-based workers (CPU-bound tasks)
tq -a 0.0.0.0 --worker-type process --log-level DEBUG
```

### 2. Run examples (same or different machine)

```sh
# Against local worker
python3 examples/01_basic_task.py

# Against remote worker
python3 examples/01_basic_task.py 192.168.122.87

# Most examples accept HOST and optional COUNT/SECONDS
python3 examples/02_concurrent_tasks.py 192.168.122.87 200
python3 examples/11_performance_bench.py 192.168.122.87
```

## Running Multiple Workers

```sh
# Terminal 1
tq -a 0.0.0.0 -p 9000 --pull-port 9001

# Terminal 2
tq -a 0.0.0.0 -p 9010 --pull-port 9011

# Terminal 3
tq -a 0.0.0.0 -p 9020 --pull-port 9021

# Then run the multi-worker example
python3 examples/08_multiple_workers.py 192.168.122.87
```

## Running with HMAC Security

```sh
# Worker with signing key (must match client)
tq -a 0.0.0.0 --signkey "my-secret-key"

# Example must use the same key
python3 examples/09_hmac_security.py 192.168.122.87
```

## Examples Index

| # | File | What it tests | Time |
|---|------|---------------|------|
| 01 | `01_basic_task.py` | Single task, connect/submit/result/disconnect | ~1s |
| 02 | `02_concurrent_tasks.py` | N async tasks, correctness, throughput | ~5s |
| 03 | `03_blocking_vs_async.py` | `put()` vs `put_blocking()` timing | ~10s |
| 04 | `04_exception_handling.py` | Exception propagation, recovery, interleaving | ~5s |
| 05 | `05_large_payloads.py` | 100KB–1MB payloads, binary, nested structures | ~15s |
| 06 | `06_delayed_tasks.py` | `delay=N` parameter, immediate vs delayed | ~8s |
| 07 | `07_interval_tasks.py` | `eta="Ns"` periodic execution | ~10s |
| 08 | `08_multiple_workers.py` | `tasq.multi_queue()` round-robin distribution | ~5s |
| 09 | `09_hmac_security.py` | `signkey` parameter, HMAC payload signing | ~3s |
| 10 | `10_complex_data.py` | Custom classes, closures, nested/mixed types | ~5s |
| 11 | `11_performance_bench.py` | Latency, throughput, burst, memory safety | ~15s |
| 12 | `12_error_recovery.py` | Recovery, pending flush, double disconnect, rapid cycles | ~10s |

## Helper Scripts

| File | Purpose |
|------|---------|
| `server.py` | Quick worker launcher (alternative to `tq runner`) |
| `worker.py` | Full CLI worker with all options documented |

## Worker Types

| Type | Flag | Best for |
|------|------|----------|
| Actor | `--type actor` (default) | I/O-bound tasks, mixed workloads |
| Process | `--type process` | CPU-bound tasks, heavy computation |

## Troubleshooting

**Connection refused:**
- Ensure the worker is running and listening on the expected ports
- Check firewall rules if running across machines
- Verify the host/port: worker logs show `ZMQBackend(zmq://0.0.0.0 in=9001 out=9000)`
- Default bind is `127.0.0.1`; remote access requires `-a 0.0.0.0`

**Tasks hang:**
- Ensure the worker and client use matching ports
- If using HMAC, both must use the same `signkey`

**Serialization errors:**
- Tasq uses cloudpickle. Functions and arguments must be picklable
- Lambda functions work because cloudpickle handles closures
- Some C extensions may not serialize — use simple Python types when possible
