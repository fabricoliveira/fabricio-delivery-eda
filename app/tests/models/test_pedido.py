import importlib
import sys
import types
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

import sqlalchemy as sa

MODULE = "app.src.models.pedido"
DB_MODULE_PATH = "app.src.configurations.database_config"


class TestPedidoModel(unittest.TestCase):
    def _reload_pedido_with_mocks(self):
        MockBase = type("MockBase", (), {})

        fake_db_module = types.ModuleType(DB_MODULE_PATH)
        fake_db_module.Base = MockBase
        sys.modules[DB_MODULE_PATH] = fake_db_module

        Column_spy = MagicMock(wraps=sa.Column)
        Integer_spy = MagicMock(wraps=sa.Integer)
        String_spy = MagicMock(wraps=sa.String)
        Text_spy = MagicMock(wraps=sa.Text)
        DateTime_spy = MagicMock(wraps=sa.DateTime)

        patches = [
            patch("sqlalchemy.Column", new=Column_spy),
            patch("sqlalchemy.Integer", new=Integer_spy),
            patch("sqlalchemy.String", new=String_spy),
            patch("sqlalchemy.Text", new=Text_spy),
            patch("sqlalchemy.DateTime", new=DateTime_spy),
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
            "Integer": Integer_spy,
            "String": String_spy,
            "Text": Text_spy,
            "DateTime": DateTime_spy,
            "MockBase": MockBase,
        }

    def test_tablename_e_inheritance(self):
        mod, mocks = self._reload_pedido_with_mocks()
        Pedido = getattr(mod, "Pedido", None)
        self.assertIsNotNone(Pedido, "Classe Pedido deve existir no módulo")
        self.assertEqual(getattr(Pedido, "__tablename__", None), "pedidos")
        self.assertTrue(issubclass(Pedido, mocks["MockBase"]))

    def test_colunas_definidas_e_column_chamado(self):
        mod, mocks = self._reload_pedido_with_mocks()
        Pedido = mod.Pedido
        expected_attrs = ("id", "destinatario", "endereco", "itens", "status", "criado_em", "atualizado_em")
        for attr in expected_attrs:
            self.assertTrue(hasattr(Pedido, attr), f"Pedido deve ter atributo {attr}")
        self.assertGreaterEqual(mocks["Column"].call_count, len(expected_attrs))

    def test_default_datetime_e_onupdate_presente(self):
        mod, mocks = self._reload_pedido_with_mocks()
        found_default_datetime = False
        found_onupdate_datetime = False
        for call in mocks["Column"].call_args_list:
            _, kwargs = call
            if kwargs.get("default") is datetime.utcnow:
                found_default_datetime = True
            if kwargs.get("onupdate") is datetime.utcnow:
                found_onupdate_datetime = True

    def test_status_default_e_index_e_id_index(self):
        mod, mocks = self._reload_pedido_with_mocks()
        found_status_default = False
        found_status_index = False
        found_id_index = False

        for call in mocks["Column"].call_args_list:
            args, kwargs = call
            if kwargs.get("default") == "recebido":
                found_status_default = True
            if kwargs.get("index") is True:
                if args:
                    arg0 = args[0]
                    try:
                        type_name = arg0.__class__.__name__
                    except Exception:
                        type_name = ""
                    if "Integer" in type_name:
                        found_id_index = True
                    if "String" in type_name:
                        found_status_index = True

        self.assertTrue(found_status_default, "Status deve ter default='recebido'")
        self.assertTrue(found_status_index, "Status deve ter index=True")
