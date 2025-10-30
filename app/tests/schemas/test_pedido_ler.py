import importlib
import unittest
from datetime import datetime
from unittest.mock import patch

MODULE = "app.src.schemas.pedido_ler"


class TestPedidoLerSchema(unittest.TestCase):
    def _reload_pedido_ler_with_mocks(self):
        FakeBaseModel = type(
            "FakeBaseModel",
            (object,),
            {"__init__": lambda self, **kwargs: self.__dict__.update(kwargs)}
        )

        p = patch("pydantic.BaseModel", new=FakeBaseModel)
        p.start()
        try:
            mod = importlib.import_module(MODULE)
            importlib.reload(mod)
        finally:
            p.stop()

        return mod, {"FakeBaseModel": FakeBaseModel}

    def test_classe_existe_e_herda_de_base_mock(self):
        mod, mocks = self._reload_pedido_ler_with_mocks()
        PedidoLer = getattr(mod, "PedidoLer", None)
        self.assertIsNotNone(PedidoLer, "Classe PedidoLer deve existir")
        self.assertTrue(issubclass(PedidoLer, mocks["FakeBaseModel"]))

    def test_model_config_from_attributes_enabled(self):
        mod, _ = self._reload_pedido_ler_with_mocks()
        PedidoLer = mod.PedidoLer
        cfg = getattr(PedidoLer, "model_config", {})
        self.assertTrue(cfg.get("from_attributes", False), "model_config deve ter from_attributes=True")

    def test_anotacoes_contem_campos_esperados(self):
        mod, _ = self._reload_pedido_ler_with_mocks()
        PedidoLer = mod.PedidoLer
        ann = getattr(PedidoLer, "__annotations__", {})
        for field in ("id", "destinatario", "endereco", "itens", "status", "criado_em"):
            self.assertIn(field, ann, f"Annotation deve conter '{field}'")

    def test_instanciacao_por_kwargs_atribui_campos(self):
        mod, _ = self._reload_pedido_ler_with_mocks()
        PedidoLer = mod.PedidoLer
        now = datetime.utcnow()
        data = {
            "id": 10,
            "destinatario": "Cliente",
            "endereco": "Rua X",
            "itens": [{"sku": "a", "qtd": 1}],
            "status": "recebido",
            "criado_em": now,
        }
        inst = PedidoLer(**data)
        self.assertEqual(inst.id, data["id"])
        self.assertEqual(inst.destinatario, data["destinatario"])
        self.assertEqual(inst.endereco, data["endereco"])
        self.assertEqual(inst.itens, data["itens"])
        self.assertEqual(inst.status, data["status"])
        self.assertIsInstance(inst.criado_em, datetime)
        self.assertAlmostEqual(inst.criado_em.timestamp(), now.timestamp(), delta=1)

    def test_instanciacao_iso_string_para_criado_em_eh_preservada_com_fake(self):
        mod, _ = self._reload_pedido_ler_with_mocks()
        PedidoLer = mod.PedidoLer
        iso = datetime.utcnow().isoformat()
        inst = PedidoLer(
            id=1,
            destinatario="A",
            endereco="B",
            itens=[],
            status="s",
            criado_em=iso,
        )
        self.assertEqual(inst.criado_em, iso)
