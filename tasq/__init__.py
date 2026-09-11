from urllib.parse import urlparse

from tasq.actors.routers import RoundRobinRouter, actor_pool
from tasq.queue import TasqMultiQueue, TasqQueue
from tasq.remote.client import Client
from tasq.remote.connection import ZMQBackendConnection
from tasq.worker.actors import ClientWorker


def queue(backend="zmq://localhost:9000", signkey=None):
    """
    Create a TasqQueue instance.
    The formats accepted for the backends are:

    - zmq://localhost:9000?pull_port=9001
    - tcp://localhost:5555
    - ipc://localhost:5555

    Attributes
    ----------
    :type backend: str or 'zmq://localhost:9000'
    :param backend: An URL to connect to for the backend service

    :type signkey: str or None
    :param signkey: A string representing a shared key, sign data with a shared
                    key
    """
    url_parsed = urlparse(backend)
    scheme = url_parsed.scheme or "zmq"
    assert scheme in ("zmq", "unix", "tcp"), f"Unsupported {scheme} as backend"
    _backend = ZMQBackendConnection.from_url(backend, signkey)
    client = Client(_backend)
    return TasqQueue(client)


def multi_queue(urls, router_class=RoundRobinRouter, signkey=None):
    assert all(isinstance(url, (tuple, str)) for url in urls), (
        "urls argument must be a tuple (host, push_port, pull_port) or a string"
    )
    backends = []
    for url in urls:
        if isinstance(url, tuple):
            host, push_port, pull_port = url
            backends.append(
                Client(ZMQBackendConnection(host, push_port, pull_port, signkey=signkey))
            )
        elif isinstance(url, str):
            url_parsed = urlparse(url)
            scheme = url_parsed.scheme or "zmq"
            assert scheme in (
                "zmq",
                "tcp",
                "unix",
            ), f"Unsupported {scheme} as backend"
            backends.append(Client(ZMQBackendConnection.from_url(url, signkey)))
    return TasqMultiQueue(
        backends,
        lambda: actor_pool(
            num_workers=len(backends),
            actor_class=ClientWorker,
            router_class=router_class,
            clients=backends,
        ),
    )
