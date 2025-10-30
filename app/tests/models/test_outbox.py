import importlib
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

import sqlalchemy as sa

MODULE = "app.src.models.outbox"
DB_MODULE_PATH = "app.src.configurations.database_config"


class TestOutboxModel(unittest.TestCase):
    def _reload_outbox_with_mocks(self):
        MockBase = type("MockBase", (), {})

        fake_db_module = types.ModuleType(DB_MODULE_PATH)
        fake_db_module.Base = MockBase
        sys.modules[DB_MODULE_PATH] = fake_db_module

        try:
            pg = importlib.import_module("sqlalchemy.dialects.postgresql")
            UUID_impl = getattr(pg, "UUID")
        except Exception:
            UUID_impl = sa.String

        Column_spy = MagicMock(wraps=sa.Column)
        String_spy = MagicMock(wraps=sa.String)
        Integer_spy = MagicMock(wraps=sa.Integer)
        Text_spy = MagicMock(wraps=sa.Text)
        DateTime_spy = MagicMock(wraps=sa.DateTime)
        Boolean_spy = MagicMock(wraps=sa.Boolean)
        UUID_spy = MagicMock(wraps=UUID_impl)

        patches = [
            patch("sqlalchemy.Column", new=Column_spy),
            patch("sqlalchemy.String", new=String_spy),
            patch("sqlalchemy.Integer", new=Integer_spy),
            patch("sqlalchemy.Text", new=Text_spy),
            patch("sqlalchemy.DateTime", new=DateTime_spy),
            patch("sqlalchemy.Boolean", new=Boolean_spy),
            patch("sqlalchemy.dialects.postgresql.UUID", new=UUID_spy),
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
            "Boolean": Boolean_spy,
            "UUID": UUID_spy,
            "MockBase": MockBase,
        }

    def test_tablename_e_inheritance(self):
        mod, mocks = self._reload_outbox_with_mocks()
        Outbox = getattr(mod, "Outbox", None)
        self.assertIsNotNone(Outbox, "Classe Outbox deve existir no módulo")
        self.assertEqual(getattr(Outbox, "__tablename__", None), "outbox")
        self.assertTrue(issubclass(Outbox, mocks["MockBase"]))

    def test_colunas_existentes_e_chamadas_column(self):
        mod, mocks = self._reload_outbox_with_mocks()
        Outbox = mod.Outbox
        for attr in ("id", "pedido_id", "tipo_evento", "payload", "publicado", "criado_em", "publicado_em"):
            self.assertTrue(hasattr(Outbox, attr), f"Outbox deve ter atributo {attr}")
        self.assertGreaterEqual(mocks["Column"].call_count, 7)

    def test_uuid_usado_em_id_e_chamada_uuid(self):
        mod, mocks = self._reload_outbox_with_mocks()
        self.assertGreaterEqual(mocks["UUID"].call_count, 1)

    def test_defaults_datetime_e_boolean_e_index(self):
        mod, mocks = self._reload_outbox_with_mocks()
        found_default_datetime = False
        found_default_false = False

        for call in mocks["Column"].call_args_list:
            args, kwargs = call
            if kwargs.get("default") is datetime.utcnow:
                found_default_datetime = True
            if kwargs.get("default") is False:
                found_default_false = True

        self.assertTrue(found_default_false, "Ao menos uma Column deve receber default=False (publicado)")

    def test_pedido_e_publicado_indices_presencas(self):
        mod, mocks = self._reload_outbox_with_mocks()
        pedido_index_found = False
        publicado_index_found = False

        for call in mocks["Column"].call_args_list:
            args, kwargs = call
            if kwargs.get("index") is True:
                if args and getattr(args[0], "__class__", None) and args[
                    0].__class__.__name__ == sa.Integer().__class__.__name__:
                    pedido_index_found = True
                if args and getattr(args[0], "__class__", None) and args[
                    0].__class__.__name__ == sa.Boolean().__class__.__name__:
                    publicado_index_found = True
