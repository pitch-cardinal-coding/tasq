"""
tasq.settings.py
~~~~~~~~~~~~~~~~
"""

import os
from typing import ClassVar

from .util import Configuration


class TasqConfig(Configuration):
    defaults: ClassVar[dict] = {
        "addr": "127.0.0.1",
        "zmq": {"push_port": 9001, "pull_port": 9000},
        "signkey": os.getenv("TASQ_SIGN_KEY", None),
        "unix": False,
        "log_level": "INFO",
        "num_workers": 4,
    }


def get_config(path=None):
    if path is None:
        path = os.getenv("TASQ_CONF", "~/.tasq/configuration.json")
    rc = TasqConfig(path)
    return rc
