"""
tasq.cli.main.py
~~~~~~~~~~~~~~~~
"""

import argparse

from ..logger import get_logger, logger
from ..remote.runner import build_zmq_actor_runner, build_zmq_queue_runner
from ..settings import get_config

log = get_logger(__name__)


def parse_arguments():
    parser = argparse.ArgumentParser(description="Tasq CLI")
    parser.add_argument(
        "--conf",
        "-c",
        help="The filepath to the configuration file, in json",
    )
    parser.add_argument(
        "--address",
        "-a",
        help="The ZMQ host address to connect to, default to localhost",
    )
    parser.add_argument(
        "--port",
        "-p",
        help="The ZMQ port to connect to, default to 9000",
        type=int,
    )
    parser.add_argument(
        "--pull-port",
        help="The ZMQ port to connect to, default to 9001",
        type=int,
    )
    parser.add_argument(
        "--worker-type",
        choices=["actor", "process"],
        default="actor",
        help="The type of worker to deploy (default: actor)",
    )
    parser.add_argument(
        "--signkey",
        help="The shared key to use to sign byte streams between clients and runners",
    )
    parser.add_argument(
        "--unix",
        "-u",
        help="Unix socket flag, in case runners and clients reside on the same node",
        action="store_true",
    )
    parser.add_argument(
        "--num-workers",
        help="Number of workers to instantiate on the node",
        type=int,
    )
    parser.add_argument("--log-level", help="Set logging level")
    args = parser.parse_args()
    return args


def start_worker(worker_type, host, channel, signkey, num_workers, unix):
    builders = {
        "actor": build_zmq_actor_runner,
        "process": build_zmq_queue_runner,
    }
    builder = builders[worker_type]
    log.info("Starting %s worker type", worker_type.upper())
    runner = builder(
        host=host,
        channel=channel,
        signkey=signkey,
        num_workers=num_workers,
        unix=unix,
    )
    runner.start()


def main():
    args = parse_arguments()
    conf = get_config(args.conf)
    logger.loglevel = args.log_level or conf["log_level"]
    signkey = args.signkey or conf["signkey"]
    unix = conf["unix"]
    num_workers = args.num_workers or conf["num_workers"]
    worker_type = args.worker_type or "actor"
    addr = args.address or conf["addr"]
    push_port = args.pull_port or conf["zmq"]["push_port"]
    pull_port = args.port or conf["zmq"]["pull_port"]
    start_worker(
        worker_type=worker_type,
        host=addr,
        channel=(push_port, pull_port),
        signkey=signkey,
        num_workers=num_workers,
        unix=unix,
    )
