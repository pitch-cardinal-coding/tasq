"""
tasq.remote.connection.py
~~~~~~~~~~~~~~~~~~~~~~~~~

This module contains the ZMQ connection class.
"""

from urllib.parse import urlparse

import zmq

from ..exception import BackendCommunicationErrorException
from .sockets import CloudPickleContext


class ZMQBackendConnection:
    """Connection class, set up two communication channels, a PUSH and a PULL
    channel using two synchronous TCP sockets. Each socket is a subclass of zmq
    sockets given the capability to handle cloudpickled data
    """

    def __init__(self, host, push_port, pull_port, unix=False, signkey=None):
        # Host address to bind sockets to
        self._host = host
        # Send digital signed data
        self._signkey = signkey
        # Port for pull side (ingoing) of the communication channel
        # Port for push side (outgoing) of the communication channel
        self._channel = (pull_port, push_port)
        self._unix = unix
        # ZMQ settings
        self._ctx = CloudPickleContext()
        self._push_socket = self._ctx.socket(zmq.PUSH)
        self._pull_socket = self._ctx.socket(zmq.PULL)

    def __repr__(self):
        protocol = "unix" if self._unix else "zmq"
        return f"ZMQBackendConnection({protocol}://{self._host}:{self._channel})"

    def connect(self):
        """Connect to the remote workers, setting up PUSH and PULL channels
        using TCP sockets, respectively used to send tasks and to retrieve
        results back
        """
        protocol = "ipc" if self._unix else "tcp"
        pull, push = self._channel
        self._pull_socket.connect(f"{protocol}://{self._host}:{pull}")
        self._push_socket.connect(f"{protocol}://{self._host}:{push}")

    def disconnect(self):
        """Disconnect PUSH and PULL sockets"""
        protocol = "ipc" if self._unix else "tcp"
        pull, push = self._channel
        self._pull_socket.disconnect(f"{protocol}://{self._host}:{pull}")
        self._push_socket.disconnect(f"{protocol}://{self._host}:{push}")

    def close(self):
        """Close sockets connected to workers, destroy zmq context"""
        self._pull_socket.close()
        self._push_socket.close()
        self._ctx.destroy()

    def send(self, data, flags=0):
        """Send data through the PUSH socket, if a signkey flag is set it sign
        it before sending
        """
        try:
            self._push_socket.send_data(data, flags, self._signkey)
        except (zmq.error.ContextTerminated, zmq.error.ZMQError) as e:
            raise BackendCommunicationErrorException(str(e))

    def recv(self, unpickle=True, flags=0):
        """Receive data from the PULL socket, if a signkey flag is set it
        checks for integrity of the received data
        """
        try:
            data = self._pull_socket.recv_data(unpickle, flags, self._signkey)
        except (zmq.error.ContextTerminated, zmq.error.ZMQError) as e:
            raise BackendCommunicationErrorException(str(e))
        else:
            return data

    def recv_result(self, unpickle=True, flags=0):
        return self.recv(unpickle, flags)

    def is_connected(self):
        return True

    @classmethod
    def from_url(cls, url, signkey=None):
        u = urlparse(url)
        scheme = u.scheme or "zmq"
        assert scheme in ("zmq", "unix", "tcp"), f"Unsupported {scheme}"
        extras = {t.split("=")[0]: t.split("=")[1] for t in u.query.split("?") if t}
        extras = {k: v for k, v in extras.items() if k == "pull_port"}
        conn_args = {
            "host": u.hostname or "127.0.0.1",
            "push_port": u.port or 9000,
            "pull_port": int(extras.get("pull_port", (u.port or 9000) + 1)),
            "unix": scheme == "unix",
            "signkey": signkey,
        }
        return cls(**conn_args)
