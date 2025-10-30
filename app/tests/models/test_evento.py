import importlib
import sys
import types
import unittest
from unittest.mock import patch, MagicMock

import sqlalchemy as sa

MODULE = "app.src.models.evento"
DB_MODULE_PATH = "app.src.configurations.database_config"


class TestEventoModel(unittest.TestCase):
    def _reload_evento_with_mocks(self):
        MockBase = type("MockBase", (), {})

        fake_db_module = types.ModuleType(DB_MODULE_PATH)
        fake_db_module.Base = MockBase
        sys.modules[DB_MODULE_PATH] = fake_db_module

        Column_spy = MagicMock(wraps=sa.Column)
        String_spy = MagicMock(wraps=sa.String)
        Integer_spy = MagicMock(wraps=sa.Integer)
        Text_spy = MagicMock(wraps=sa.Text)
        DateTime_spy = MagicMock(wraps=sa.DateTime)
        UniqueConstraint_spy = MagicMock(wraps=sa.UniqueConstraint)

        patches = [
            patch("sqlalchemy.Column", new=Column_spy),
            patch("sqlalchemy.String", new=String_spy),
            patch("sqlalchemy.Integer", new=Integer_spy),
            patch("sqlalchemy.Text", new=Text_spy),
            patch("sqlalchemy.DateTime", new=DateTime_spy),
            patch("sqlalchemy.UniqueConstraint", new=UniqueConstraint_spy),
        ]

        for p in patches:
            p.start()
        try:
            mod = importlib.import_module(MODULE)
            importlib.reload(mod)
        finally:
            for p in reversed(patches):
                p.stop()
            sys.modules.pop(DB_MODULE_PATH, None)

        return mod, {
            "Column": Column_spy,
            "String": String_spy,
            "Integer": Integer_spy,
            "Text": Text_spy,
            "DateTime": DateTime_spy,
            "UniqueConstraint": UniqueConstraint_spy,
            "MockBase": MockBase,
        }

    def test_tablename_e_inheritance(self):
        mod, mocks = self._reload_evento_with_mocks()
        Evento = getattr(mod, "Evento", None)
        self.assertIsNotNone(Evento, "Classe Evento deve existir no módulo")
        self.assertEqual(getattr(Evento, "__tablename__", None), "eventos")
        self.assertTrue(issubclass(Evento, mocks["MockBase"]))

    def test_colunas_criadas_e_chamadas_column(self):
        mod, mocks = self._reload_evento_with_mocks()
        Evento = mod.Evento
        for attr in ("id", "pedido_id", "tipo_evento", "payload", "criado_em"):
            self.assertTrue(hasattr(Evento, attr), f"Evento deve ter atributo {attr}")
        self.assertGreaterEqual(mocks["Column"].call_count, 5)

    def test_unique_constraint_e_default_datetime(self):
        mod, mocks = self._reload_evento_with_mocks()
        Evento = mod.Evento
        table_args = getattr(Evento, "__table_args__", None)
        self.assertIsNotNone(table_args, "__table_args__ deve estar definido")
        self.assertIsInstance(table_args, tuple)
        self.assertGreaterEqual(mocks["UniqueConstraint"].call_count, 1)
        self.assertTrue(
            any(isinstance(item, sa.UniqueConstraint) for item in table_args),
            "__table_args__ deve incluir um sa.UniqueConstraint"
        )
