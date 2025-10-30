import asyncio
import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock

MODULE = "app.src.services.publisher_service"


class FakeOutbox:
    def __init__(self, id=None, payload=None, pedido_id=None):
        self.id = id
        self.payload = payload
        self.pedido_id = pedido_id


class FakeExchange:
    def __init__(self, publish_behaviour=None):
        self.publish_behaviour = publish_behaviour or (lambda msg, routing_key="": None)
        self.published = []

    async def publish(self, message, routing_key=""):
        self.published.append((message, routing_key))
        return self.publish_behaviour(message, routing_key)


class FakeChannel:
    def __init__(self, exchange_obj):
        self._exchange_obj = exchange_obj

    async def declare_exchange(self, *a, **k):
        return self._exchange_obj

    async def declare_queue(self, *a, **k):
        return SimpleNamespace()


class FakeConnectionCM:
    def __init__(self, conn_obj):
        self._conn = conn_obj

    async def __aenter__(self):
        return self._conn

    async def __aexit__(self, exc_type, exc, tb):
        return False


class FakeConnection:
    def __init__(self, channel_obj):
        self._channel_obj = channel_obj

    async def channel(self):
        return self._channel_obj


class TestPublisherService(unittest.TestCase):
    def _reload_module(self):
        mod = importlib.import_module(MODULE)
        importlib.reload(mod)
        return mod

    def test_publicar_outbox_trata_erro_no_publish_e_nao_marca(self):
        mod = self._reload_module()

        out = FakeOutbox(id=2, payload='x', pedido_id=99)
        calls = {"n": 0}

        def fake_obter(limit):
            if calls["n"] == 0:
                calls["n"] += 1
                return [out]
            raise asyncio.CancelledError()

        def publish_raises(message, routing_key=""):
            raise RuntimeError("publish fail")

        failing_exchange = FakeExchange(publish_behaviour=lambda m, rk="": publish_raises(m, rk))
        fake_channel = FakeChannel(failing_exchange)
        fake_conn = FakeConnection(fake_channel)
        conn_cm = FakeConnectionCM(fake_conn)

        async def fake_connect_robust(url):
            return conn_cm

        async def fake_to_thread(func, *args, **kwargs):
            return func(*args, **kwargs)

        marcar_mock = MagicMock()

        with patch(f"{MODULE}.aio_pika.connect_robust", new=fake_connect_robust), \
                patch(f"{MODULE}.obter_eventos_outbox_pendentes", new=fake_obter), \
                patch(f"{MODULE}.asyncio.to_thread", new=fake_to_thread), \
                patch(f"{MODULE}.marcar_outbox_como_publicado", new=marcar_mock):
            try:
                asyncio.run(mod.publicar_outbox_loop(poll_interval=0.01))
            except asyncio.CancelledError:
                pass

        self.assertEqual(marcar_mock.call_count, 0,
                         "marcar_outbox_como_publicado não deve ser chamado se publish falha")
