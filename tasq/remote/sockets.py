"""
tasq.remote.sockets.py
~~~~~~~~~~~~~~~~~~~~~~
Here are defined some wrapper for ZMQ sockets which can handle serialization
with cloudpickle
"""

import zmq
from zmq.asyncio import Context, Socket

import tasq.remote.serializer as serde

from ..settings import get_config

# Get the configuration singleton
conf = get_config()


class CloudPickleSocket(zmq.Socket):
    """ZMQ socket adapted to send and receive cloudpickle serialized and
    compress data
    """

    def send_data(self, data, flags=0, signkey=None):
        """Serialize `data` with cloudpickle and compress it before sending
        through the socket
        """
        serialized = serde.dumps(data)
        if signkey:
            signed = serde.sign(signkey.encode(), serialized)
            return self.send_pyobj((signed, serialized), flags=flags)
        return self.send_pyobj(serialized, flags=flags)

    def recv_data(self, unpickle=True, flags=0, signkey=None):
        if signkey:
            payload = self.recv_pyobj(flags)
            recv_digest, serialized = payload
            serde.verifyhmac(signkey.encode(), recv_digest, serialized)
        else:
            serialized = self.recv_pyobj(flags)
        if unpickle:
            return serde.loads(serialized)
        return serialized


class CloudPickleContext(zmq.Context):
    _socket_class = CloudPickleSocket


class AsyncCloudPickleSocket(Socket):
    """ZMQ socket adapted to send and receive cloudpickle serialized and
    compress data in an asynchronous way
    """

    async def send_data(self, data, flags=0, signkey=None):
        """Serialize `data` with cloudpickle and compress it before sending it
        asynchronously through the socket
        """
        serialized = serde.dumps(data)
        if signkey:
            signed = serde.sign(signkey.encode(), serialized)
            return await self.send_pyobj((signed, serialized), flags=flags)
        return await self.send_pyobj(serialized, flags=flags)

    async def recv_data(self, unpickle=True, flags=0, signkey=None):
        if signkey:
            payload = await self.recv_pyobj(flags)
            recv_digest, serialized = payload
            serde.verifyhmac(signkey.encode(), recv_digest, serialized)
        else:
            serialized = await self.recv_pyobj(flags)
        return serde.loads(serialized) if unpickle else serialized


class AsyncCloudPickleContext(Context):
    _socket_class = AsyncCloudPickleSocket
