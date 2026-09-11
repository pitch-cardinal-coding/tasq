"""
tasq.queue.py
~~~~~~~~~~~~~
The main client module, provides interfaces to instantiate queues
"""

from .job import Job


class TasqQueue:
    """Main queue abstraction wrapping a ZMQ backend connection.

    Attributes
    ----------
    :type backend: tasq.remote.client.Client
    :param backend: A Client connected to a ZMQ backend
    """

    def __init__(self, backend):
        self._backend = backend
        self._backend.connect()

    def __repr__(self):
        return f"TasqQueue({self._backend})"

    def __len__(self):
        return len(self.pending_jobs())

    def is_connected(self):
        return self._backend.is_connected()

    def connect(self):
        if not self._backend.is_connected():
            self._backend.connect()

    def disconnect(self):
        if self._backend.is_connected():
            self._backend.disconnect()

    def put(self, func, *args, **kwargs):
        return self._backend.schedule(func, *args, **kwargs)

    def put_blocking(self, func, *args, **kwargs):
        return self._backend.schedule_blocking(func, *args, **kwargs)

    def pending_jobs(self):
        return list(self._backend.pending_jobs())

    def results(self):
        return self._backend.results


class TasqMultiQueue:
    def __init__(self, backends, router_factory):
        self._backends = backends
        self._router = router_factory()

    def __len__(self):
        return sum(len(b.pending_jobs()) for b in self._backends)

    def is_connected(self):
        return any(backend.is_connected() for backend in self._backends)

    def connect(self):
        for backend in self._backends:
            backend.connect()

    def disconnect(self):
        for backend in self._backends:
            backend.disconnect()

    def pending_jobs(self):
        jobs = []
        for backend in self._backends:
            jobs.extend(backend.pending_jobs())
        return jobs

    def put(self, func, *args, **kwargs):
        name = kwargs.pop("name", "")
        job = Job(name, func, *args, **kwargs)
        future = self._router.route(job)
        return future

    def put_blocking(self, func, *args, **kwargs):
        timeout = kwargs.pop("timeout", None)
        future = self.put(func, *args, **kwargs)
        result = future.result(timeout)
        return result

    def results(self):
        return [backend.results for backend in self._backends]
