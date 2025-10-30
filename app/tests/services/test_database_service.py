import importlib
import unittest
from types import SimpleNamespace

MODULE_PATH = "app.src.services.database_service"


class FakeBeginCM:
    def __init__(self, session):
        self.session = session

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeSession:
    def __init__(self, *, execute_rows=None, get_map=None, raise_on_add=False, raise_on_execute=False):
        self.execute_rows = execute_rows or []
        self.get_map = get_map or {}
        self.closed = False
        self.last_added = None
        self.raise_on_add = raise_on_add
        self.raise_on_execute = raise_on_execute

    def begin(self):
        return FakeBeginCM(self)

    def add(self, obj):
        if self.raise_on_add:
            raise importlib.import_module(MODULE_PATH).IntegrityError("simulated", params=None, orig=None)
        self.last_added = obj

    def flush(self):
        if self.last_added is not None and getattr(self.last_added, "id", None) is None:
            try:
                self.last_added.id = 1
            except Exception:
                pass

    def refresh(self, obj):
        return None

    def get(self, cls, key):
        return self.get_map.get((cls, key), self.get_map.get(key))

    def execute(self, stmt):
        if self.raise_on_execute:
            raise importlib.import_module(MODULE_PATH).OperationalError("sim", params=None, orig=None)

        class Res:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        return Res(self.execute_rows)

    def close(self):
        self.closed = True


class FakePedido:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeOutbox:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class FakeEvento:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestDatabaseService(unittest.TestCase):
    def setUp(self):
        self.mod = importlib.import_module(MODULE_PATH)
        importlib.reload(self.mod)
        self.mod.DB_PRONTO = False
        self.mod.Pedido = FakePedido
        self.mod.Outbox = FakeOutbox
        self.mod.Evento = FakeEvento

        class FakeMeta:
            def __init__(self):
                self.called = False

            def create_all(self, bind=None):
                self.called = True

        self.fake_meta = FakeMeta()
        self.mod.Base = SimpleNamespace(metadata=self.fake_meta)
        self.mod.engine = object()

        class DummyStmt:
            def where(self, *a, **k):
                return self

            def order_by(self, *a, **k):
                return self

            def limit(self, *a, **k):
                return self

        self.mod.select = lambda *a, **k: DummyStmt()

    def test_inicializar_db_sucesso(self):
        res = self.mod.inicializar_db(tentativas=1, backoff_segundos=0)
        self.assertTrue(res)
        self.assertTrue(self.mod.DB_PRONTO)
        self.assertTrue(self.fake_meta.called)

    def test_inicializar_db_retries_e_falha(self):
        def raise_op(*a, **k):
            raise self.mod.OperationalError("sim", params=None, orig=None)

        self.mod.Base.metadata.create_all = raise_op
        self.mod.sleep = lambda *_: None
        res = self.mod.inicializar_db(tentativas=2, backoff_segundos=0)
        self.assertFalse(res)
        self.assertFalse(self.mod.DB_PRONTO)

    def test_criar_pedido_com_outbox_cria_pedido_e_outbox(self):
        fake_session = FakeSession()
        self.mod.SessionLocal = lambda: fake_session

        pedido = self.mod.criar_pedido_com_outbox("João", "Rua X", [{"sku": "a"}], tipo_evento="T")
        self.assertIsNotNone(pedido)
        self.assertEqual(pedido.destinatario, "João")
        self.assertIsInstance(pedido.itens, str)
        self.assertEqual(pedido.id, 1)

    def test_obter_pedido_quando_db_nao_pronto_retorna_none(self):
        self.mod.DB_PRONTO = False
        res = self.mod.obter_pedido(10)
        self.assertIsNone(res)

    def test_salvar_evento_quando_db_nao_pronto_lanca_operationalerror(self):
        self.mod.DB_PRONTO = False
        with self.assertRaises(self.mod.OperationalError):
            self.mod.salvar_evento("ev1", 1, "t")

    def test_salvar_evento_grava_corretamente_e_trata_integrityerror(self):
        fake_session_success = FakeSession(get_map={})
        self.mod.SessionLocal = lambda: fake_session_success
        self.mod.DB_PRONTO = True
        ev = self.mod.salvar_evento("evx", 5, "t", payload={"a": 1})
        self.assertIsNotNone(ev)
        existing = FakeEvento(id="evx", pedido_id=5)
        fake_session_fail = FakeSession(get_map={("Evento", "evx"): existing}, raise_on_add=True)
        fake_session_fail.get_map = {(self.mod.Evento, "evx"): existing}
        self.mod.SessionLocal = lambda: fake_session_fail
        res = self.mod.salvar_evento("evx", 5, "t", payload=None)
        self.assertIs(res, existing)

    def test_marcar_outbox_como_publicado_true_e_false(self):
        out = FakeOutbox(id=10, publicado=False)
        fake_session = FakeSession(get_map={(self.mod.Outbox, 10): out})
        self.mod.SessionLocal = lambda: fake_session
        self.mod.DB_PRONTO = True
        ok = self.mod.marcar_outbox_como_publicado(10)
        self.assertTrue(ok)
        self.assertTrue(out.publicado)
        self.assertIsNotNone(out.publicado_em)

        fake_session2 = FakeSession(get_map={})
        self.mod.SessionLocal = lambda: fake_session2
        self.mod.DB_PRONTO = True
        ok2 = self.mod.marcar_outbox_como_publicado(999)
        self.assertFalse(ok2)

    def test_atualizar_status_pedido_true_e_false(self):
        p = FakePedido(id=5, status="recebido")
        fake_session = FakeSession(get_map={(self.mod.Pedido, 5): p})
        self.mod.SessionLocal = lambda: fake_session
        self.mod.DB_PRONTO = True
        ok = self.mod.atualizar_status_pedido(5, "entregue")
        self.assertTrue(ok)
        self.assertEqual(p.status, "entregue")

        fake_session2 = FakeSession(get_map={})
        self.mod.SessionLocal = lambda: fake_session2
        self.mod.DB_PRONTO = True
        ok2 = self.mod.atualizar_status_pedido(999, "x")
        self.assertFalse(ok2)
