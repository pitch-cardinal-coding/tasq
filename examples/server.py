#!/usr/bin/env python3
"""
server.py — Quick server script for running all examples.

Starts a worker on the default ports (9000/9001) so you can test examples
without needing the CLI.

Usage:
  python3 server.py [HOST] [PORT]

Then in another terminal:
  python3 01_basic_task.py
"""

import os
import signal
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasq.remote.runner import build_zmq_actor_runner


def main():
    host = sys.argv[1] if len(sys.argv) > 1 else "0.0.0.0"
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 9000
    pull_port = port + 1

    from tasq.logger import logger
    logger.loglevel = "INFO"

    runner = build_zmq_actor_runner(
        host=host,
        channel=(port, pull_port),
    )

    print(f"Worker starting on {host}:{port} (results: {pull_port})")
    print("Press Ctrl+C to stop")

    def handle_signal(sig, frame):
        print("\nStopping...")
        runner.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    runner.start()


if __name__ == "__main__":
    main()
