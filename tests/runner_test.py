import unittest
from concurrent.futures import Future
from unittest.mock import patch

from tasq.remote.runner import ZMQRunner, build_zmq_actor_runner, build_zmq_queue_runner


class FakeWorker:
    def route(self, job):
        fut = Future()
        fut.set_result(job.execute())
        return fut


class RunnerTest(unittest.TestCase):
    def test_build_zmq_actor_runner(self):
        with (
            patch("tasq.remote.runner.ZMQBackend") as zmqmock,
            patch("tasq.remote.runner.asyncio.get_event_loop") as loopmock,
            patch("tasq.remote.runner.actors.get_actorsystem") as ctxmock,
        ):
            loopmock.return_value = None
            zmqmock.return_value = None
            ctxmock.return_value = None
            runner = build_zmq_actor_runner(host="localhost", channel=(20000, 20001))
            self.assertIsInstance(runner, ZMQRunner)

    def test_build_zmq_queue_runner(self):
        with (
            patch("tasq.remote.runner.ZMQBackend") as zmqmock,
            patch("tasq.remote.runner.asyncio.get_event_loop") as loopmock,
            patch("tasq.remote.runner.worker.build_jobqueue") as jq,
        ):
            jq.return_value = None
            loopmock.return_value = None
            zmqmock.return_value = None
            runner = build_zmq_queue_runner(host="localhost", channel=(20000, 20001))
            self.assertIsInstance(runner, ZMQRunner)
