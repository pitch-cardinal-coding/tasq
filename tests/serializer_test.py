import unittest

import tasq.remote.serializer as serde
from tasq.exception import SignatureNotValidException


class TestSerializer(unittest.TestCase):
    def test_serde_dumps_loads(self):
        base = lambda x, y: (x + y) / 2
        dump_base = serde.dumps(base)
        self.assertTrue(isinstance(dump_base, bytes))
        self.assertEqual(base(1, 2), serde.loads(dump_base)(1, 2))

    def test_serde_sign_verify(self):
        base = lambda x, y: (x + y) / 2
        dumped = serde.dumps(base)
        digest = serde.sign(b"test-key", dumped)
        self.assertTrue(isinstance(digest, bytes))
        self.assertIsNone(serde.verifyhmac(b"test-key", digest, dumped))

    def test_serde_sign_verify_wrong_key(self):
        base = lambda x, y: (x + y) / 2
        dumped = serde.dumps(base)
        digest = serde.sign(b"test-key", dumped)
        self.assertTrue(isinstance(digest, bytes))
        with self.assertRaises(SignatureNotValidException):
            self.assertEqual(digest, serde.verifyhmac(b"wrong-key", digest, dumped))
