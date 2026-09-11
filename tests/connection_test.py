import unittest
from unittest.mock import patch

from tasq.remote.connection import ZMQBackendConnection

from .backend_test import FakeSocket


class TestConnection(unittest.TestCase):
    def test_zmqconnection_from_url(self):
        conn = ZMQBackendConnection.from_url("zmq://localhost:9000?pull_port=9001")
        self.assertEqual(conn._channel, (9001, 9000))
        self.assertEqual(conn._host, "localhost")
        self.assertEqual(conn._signkey, None)
        self.assertEqual(conn._unix, False)
        conn = ZMQBackendConnection.from_url("unix://localhost:9000?pull_port=9001")
        self.assertEqual(conn._unix, True)
        conn = ZMQBackendConnection.from_url("unix://localhost:9000")
        self.assertEqual(conn._channel, (9001, 9000))
        with self.assertRaises(AssertionError):
            conn = ZMQBackendConnection.from_url("zmw://localhost:9000?pull_port=9002")

    def test_zmqconnection_connect(self):
        fake_socket = FakeSocket()
        with patch("tasq.remote.connection.CloudPickleContext.socket") as mock:
            mock.return_value = fake_socket
        conn = ZMQBackendConnection("1.2.3.4", 20000, 20001)
        self.assertEqual(str(conn), "ZMQBackendConnection(zmq://1.2.3.4:(20001, 20000))")
        conn.connect()
        self.assertEqual(fake_socket.bind_url, "")
        conn.disconnect()
        self.assertEqual(fake_socket.dc_url, "")
