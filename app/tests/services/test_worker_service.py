import asyncio
import importlib
import unittest

MODULE = "app.src.services.worker_service"


class FakeBeginCM:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self):
        self.closed = False
        self.last_added = None

    def begin(self):
        return FakeBeginCM(self)

    def add(self, obj):
        self.last_added = obj

    def flush(self):
        if self.last_added is not None and getattr(self.last_added, "id", None) is None:
            try:
                self.last_added.id = 1
            except Exception:
                pass

    def close(self):
        self.closed = True


class FakeOutbox:
    def __init__(self, pedido_id=None, tipo_evento=None, payload=None):
        self.pedido_id = pedido_id
        self.tipo_evento = tipo_evento
        self.payload = payload
        self.id = None
        self.publicado = False
        self.publicado_em = None


class StopLoop(BaseException):
    """Exceção derivada de BaseException para escapar dos except Exception do loop e encerrar test."""


class TestWorkerService(unittest.TestCase):
    def setUp(self):
        self.mod = importlib.import_module(MODULE)
        importlib.reload(self.mod)

    def test_enfileirar_pedido_coloca_na_fila(self):
        self.mod.pedido_queue = asyncio.Queue()
        self.mod.enfileirar_pedido(42)
        item = self.mod.pedido_queue.get_nowait()
        self.assertEqual(item, 42)

    def test_processar_pedidos_cria_outbox_e_atualiza_status_e_para_por_stop(self):
        fake_session = FakeSession()
        self.mod.SessionLocal = lambda: fake_session
        self.mod.Outbox = FakeOutbox

        self.mod.pedido_queue = asyncio.Queue()
        self.mod.enfileirar_pedido(123)

        async def fake_sleep(delay):
            return None

        self.mod.asyncio.sleep = fake_sleep

        calls = {"n": 0}

        async def fake_to_thread(func, *a, **k):
            calls["n"] += 1
            result = func(*a, **k)
            if calls["n"] >= 2:
                raise StopLoop()
            return result

        self.mod.asyncio.to_thread = fake_to_thread

        def fake_atualizar_status_pedido(pid, status):
            return True

        self.mod.atualizar_status_pedido = fake_atualizar_status_pedido

        try:
            asyncio.run(self.mod.processar_pedidos_loop())
        except StopLoop:
            pass

        self.assertIsNotNone(fake_session.last_added, "Outbox deve ter sido adicionado à sessão")
        self.assertIsInstance(fake_session.last_added, FakeOutbox)
        self.assertEqual(fake_session.last_added.pedido_id, 123)
        self.assertEqual(fake_session.last_added.id, 1)
