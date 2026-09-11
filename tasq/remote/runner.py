"""
tasq.remote.runner.py
~~~~~~~~~~~~~~~~~~~~~
Runner process, listening for incoming connections to schedule tasks to a pool
of worker actors
"""

import asyncio
import os
from multiprocessing import cpu_count

from tasq import actors, worker

from ..logger import get_logger
from .backend import ZMQBackend


def max_workers():
    return (cpu_count() * 2) + 1


class Runner:
    def __init__(self, backend, worker_factory, unpickle=True, signkey=None):
        self._signkey = signkey
        self._backend = backend
        self._workers = worker_factory()
        self._run = False
        self._unpickle = unpickle
        self._log = get_logger(f"{__name__}-{os.getpid()}")

    def _respond(self, fut):
        self._backend.send_result(fut.result())

    def stop(self):
        self._log.info("Stopping..")
        self._run = False
        self._backend.stop()

    def start(self):
        self._run = True
        self._log.debug("Listening on %s", self._backend)
        self.run()

    def run(self):
        while self._run:
            job = self._backend.recv(5, unpickle=self._unpickle)
            if not job:
                continue
            self._log.debug("Received job: %s", job)
            fut = self._workers.route(job)
            fut.add_done_callback(self._respond)


class ZMQRunner:
    """Runner process, handle requests asynchronously from clients and
    delegate processing of incoming tasks to worker processes, responses are
    sent back to clients by using a dedicated thread
    """

    def __init__(self, backend, worker_factory, unpickle=True, signkey=None):
        self._signkey = signkey
        self._backend = backend
        self._workers = worker_factory()
        self._unpickle = unpickle
        self._run = False
        self._log = get_logger(f"{__name__}-{os.getpid()}")
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    def stop(self):
        self._log.info("Stopping..")
        self._run = False
        for task in asyncio.all_tasks(self._loop):
            task.cancel()
        self._loop.stop()
        self._loop.close()
        self._backend.stop()

    def start(self):
        self._backend.bind()
        self._run = True
        self._log.info(self._backend)
        self._loop.create_task(self.run())
        self._loop.run_forever()

    async def run(self):
        while self._run:
            try:
                if await self._backend.poll():
                    job = await self._backend.recv(unpickle=self._unpickle)
                    self._log.debug("Received job: %s", job)
                    f = self._workers.route(job)
                    fut = asyncio.wrap_future(f)
                    await self._backend.send(await fut)
            except asyncio.CancelledError:
                pass


def build_zmq_actor_runner(
    host,
    channel,
    router_class=actors.RoundRobinRouter,
    num_workers=None,
    signkey=None,
    unix=False,
    unpickle=True,
):
    if num_workers is None:
        num_workers = max_workers()
    push, pull = channel
    ctx = actors.get_actorsystem(f"{host}:({push}, {pull})")
    server = ZMQBackend(host, push, pull, signkey, unix)
    return ZMQRunner(
        server,
        lambda: worker.build_worker_actor_router(router_class, num_workers, ctx),
        unpickle,
        signkey,
    )


def build_zmq_queue_runner(
    host,
    channel,
    num_workers=None,
    signkey=None,
    unix=False,
    unpickle=False,
):
    if num_workers is None:
        num_workers = max_workers()
    push, pull = channel
    server = ZMQBackend(host, push, pull, signkey, unix)
    return ZMQRunner(server, lambda: worker.build_jobqueue(num_workers), unpickle, signkey)
