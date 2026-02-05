import asyncio
import json
import unittest
from unittest.mock import patch

from util.client_cosmic import Cosmic
from util.client_send_audio import send_message


class DummyState:
    def __init__(self, name="OPEN"):
        self.name = name


class DummyWSBroken:
    def __init__(self):
        self.state = DummyState("OPEN")
        self.closed = False
        self.calls = 0

    async def send(self, msg):
        self.calls += 1
        raise BrokenPipeError(32, "Broken pipe")


class DummyWSOK:
    def __init__(self):
        self.state = DummyState("OPEN")
        self.closed = False
        self.sent = None

    async def send(self, msg):
        self.sent = msg


class TestClientSendMessage(unittest.TestCase):
    def test_send_message_reconnect_on_broken_pipe(self):
        async def run_send_and_check():
            Cosmic.websocket = DummyWSBroken()
            ok_ws = DummyWSOK()

            async def fake_check_websocket():
                Cosmic.websocket = ok_ws
                return True

            message = {"task_id": "t", "is_final": False, "data": "x"}
            with patch("util.client_send_audio.check_websocket", fake_check_websocket):
                await send_message(message)
            self.assertEqual(ok_ws.sent, json.dumps(message))

        asyncio.run(run_send_and_check())
