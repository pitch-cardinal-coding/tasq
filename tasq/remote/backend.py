"""
tasq.remote.backend.py
~~~~~~~~~~~~~~~~~~~~~~

This module contains the ZMQ backend implementation.
"""

try:
    import zmq
except ImportError:
    print("You need to install zmq python driver to use ZMQ backend")


from .sockets import AsyncCloudPickleContext


class ZMQBackend:
    """Connection class, set up two communication channels, a PUSH one using a
    synchronous socket and a PULL one using an asynchronous socket. Each socket
    is a subclass of zmq sockets given the capability to handle cloudpickled
    data
    """

    def __init__(self, host, push_port, pull_port, signkey=None, unix=False):
        # Host address to bind sockets to
        self._host = host
        # Send digital signed data
        self._signkey = signkey
        # Port for pull side (ingoing) of the communication channel
        self._pull_port = pull_port
        # Port for push side (outgoing) of the communication channel
        self._push_port = push_port
        # ZMQ settings
        self._ctx = AsyncCloudPickleContext()
        self._push_socket = self._ctx.socket(zmq.PUSH)
        self._pull_socket = self._ctx.socket(zmq.PULL)
        # ZMQ poller settings for async recv
        self._poller = zmq.asyncio.Poller()
        self._poller.register(self._pull_socket, zmq.POLLIN)
        self._unix = unix

    def __repr__(self):
        protocol = "ipc" if self._unix else "zmq"
        return f"ZMQBackend({protocol}://{self._host} in={self._push_port} out={self._pull_port})"

    def bind(self):
        """Bind PUSH socket on push_port (sends results to clients) and
        PULL socket on pull_port (receives tasks from clients)"""
        protocol = "tcp" if not self._unix else "ipc"
        self._push_socket.bind(f"{protocol}://{self._host}:{self._push_port}")
        self._pull_socket.bind(f"{protocol}://{self._host}:{self._pull_port}")

    def stop(self):
        # Close connected sockets
        self._pull_socket.close()
        self._push_socket.close()
        # Destroy the contexts
        self._ctx.destroy()

    async def poll(self):
        events = await self._poller.poll()
        if self._pull_socket in dict(events):
            return dict(events)
        return None

    async def send(self, data, flags=0):
        """Send data through the PUSH socket, if a signkey flag is set it sign
        it before sending
        """
        await self._push_socket.send_data(data, flags, self._signkey)

    async def recv(self, unpickle=True, flags=0):
        """Asynchronous receive data from the PULL socket, if a signkey flag is
        set it checks for integrity of the received data
        """
        return await self._pull_socket.recv_data(unpickle, flags, self._signkey)
