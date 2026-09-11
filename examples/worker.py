#!/usr/bin/env python3
"""
worker.py — Start a tasq worker with configurable options.

Usage:
  python3 worker.py [OPTIONS]

Options:
  --host HOST         Bind address (default: 0.0.0.0)
  --port PORT         PUSH port for incoming tasks (default: 9000)
  --pull-port PORT    PULL port for outgoing results (default: 9001)
  --type TYPE         Worker type: actor or process (default: actor)
  --workers N         Number of worker threads/processes (default: auto)
  --signkey KEY       HMAC signing key
  --log-level LEVEL   Logging level (default: INFO)
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasq.remote.runner import build_zmq_actor_runner, build_zmq_queue_runner


def main():
    parser = argparse.ArgumentParser(description="Start a tasq worker")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=9000, help="PUSH port (tasks in)")
    parser.add_argument("--pull-port", type=int, default=9001, help="PULL port (results out)")
    parser.add_argument("--type", choices=["actor", "process"], default="actor", help="Worker type")
    parser.add_argument("--workers", type=int, default=None, help="Number of workers")
    parser.add_argument("--signkey", default=None, help="HMAC signing key")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    args = parser.parse_args()

    from tasq.logger import logger
    logger.loglevel = args.log_level

    builders = {"actor": build_zmq_actor_runner, "process": build_zmq_queue_runner}
    runner = builders[args.type](
        host=args.host,
        channel=(args.port, args.pull_port),
        signkey=args.signkey,
        num_workers=args.workers,
    )
    print(f"Starting {args.type} worker on {args.host}:{args.port}/{args.pull_port}")
    if args.workers:
        print(f"  Workers: {args.workers}")
    if args.signkey:
        print("  HMAC: enabled")
    print("Press Ctrl+C to stop")

    try:
        runner.start()
    except KeyboardInterrupt:
        print("\nStopping...")
        runner.stop()


if __name__ == "__main__":
    main()
