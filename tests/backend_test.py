import asyncio
import unittest
from unittest.mock import patch

from tasq.remote.backend import ZMQBackend


class FakeSocket:
    def __init__(self):
        self.bind_url = ""
        self.dc_url = ""
        self.data_sent = None

    async def send_data(self, data, flags, signkey):
        self.data_sent = (data, flags, signkey)

    async def recv_data(self, unpickle, flags, signkey):
        return self.data_sent

    def bind(self, url):
        self.bind_url = url

    def connect(self, url):
        self.bind_url = url

    def disconnect(self, url):
        self.dc_url = url

    def close(self):
        pass


class TestZMQBackend(unittest.TestCase):
    def test_init_zmqbackend(self):
        with patch("tasq.remote.backend.AsyncCloudPickleContext.socket") as mock:
            mock.side_effect = lambda _: FakeSocket()
            backend = ZMQBackend("localhost", 10000, 10001)
            backend.bind()
            self.assertEqual(backend._push_socket.bind_url, "tcp://localhost:10000")
            self.assertEqual(backend._pull_socket.bind_url, "tcp://localhost:10001")
            backend.stop()

    def test_send_zmqbackend(self):
        fake_socket = FakeSocket()
        with patch("tasq.remote.backend.AsyncCloudPickleContext.socket") as mock:
            mock.return_value = fake_socket
            backend = ZMQBackend("localhost", 10000, 10001)
            backend.bind()
            asyncio.run(backend.send("hello"))
            self.assertEqual(fake_socket.data_sent, ("hello", 0, None))

    def test_recv_zmqbackend(self):
        fake_socket = FakeSocket()
        with patch("tasq.remote.backend.AsyncCloudPickleContext.socket") as mock:
            mock.return_value = fake_socket
            backend = ZMQBackend("localhost", 10000, 10001)
            backend.bind()
            asyncio.run(backend.send("hello"))
            self.assertEqual(fake_socket.data_sent, ("hello", 0, None))
            payload = asyncio.run(backend.recv())
            self.assertEqual(payload, ("hello", 0, None))
