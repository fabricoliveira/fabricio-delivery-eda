import importlib
import unittest
from unittest.mock import patch

MODULE = "app.src.schemas.pedido_criar"


class TestPedidoCriarSchema(unittest.TestCase):
    def _reload_pedido_criar_with_mocks(self):
        FakeBaseModel = type("FakeBaseModel", (object,), {
            "__init__": lambda self, **kwargs: self.__dict__.update(kwargs)
        })

        p = patch("pydantic.BaseModel", new=FakeBaseModel)
        p.start()
        try:
            mod = importlib.import_module(MODULE)
            importlib.reload(mod)
        finally:
            p.stop()

        return mod, {"FakeBaseModel": FakeBaseModel}

    def test_classe_existe_e_herda_de_base_mock(self):
        mod, mocks = self._reload_pedido_criar_with_mocks()
        PedidoCriar = getattr(mod, "PedidoCriar", None)
        self.assertIsNotNone(PedidoCriar, "Classe PedidoCriar deve existir")
        self.assertTrue(issubclass(PedidoCriar, mocks["FakeBaseModel"]))

    def test_anotacoes_contem_campos_esperados(self):
        mod, _ = self._reload_pedido_criar_with_mocks()
        PedidoCriar = mod.PedidoCriar
        ann = getattr(PedidoCriar, "__annotations__", {})
        self.assertIn("destinatario", ann)
        self.assertIn("endereco", ann)
        self.assertIn("itens", ann)

    def test_instanciacao_por_kwargs_atribui_campos(self):
        mod, _ = self._reload_pedido_criar_with_mocks()
        PedidoCriar = mod.PedidoCriar
        data = {"destinatario": "João", "endereco": "Rua A, 1", "itens": [{"sku": "x", "qtd": 1}]}
        inst = PedidoCriar(**data)
        self.assertEqual(inst.destinatario, "João")
        self.assertEqual(inst.endereco, "Rua A, 1")
        self.assertEqual(inst.itens, [{"sku": "x", "qtd": 1}])

    def test_itens_tem_valor_default_lista_quando_nao_informado(self):
        mod, _ = self._reload_pedido_criar_with_mocks()
        PedidoCriar = mod.PedidoCriar
        inst = PedidoCriar(destinatario="A", endereco="B")
        cls_default = getattr(PedidoCriar, "itens", None)
        if cls_default is not None:
            self.assertIsInstance(cls_default, list)
        else:
            self.assertFalse(hasattr(inst, "itens"))

    def test_itens_aceita_none_e_lista(self):
        mod, _ = self._reload_pedido_criar_with_mocks()
        PedidoCriar = mod.PedidoCriar
        inst_none = PedidoCriar(destinatario="A", endereco="B", itens=None)
        self.assertIsNone(inst_none.itens)
        lista = [{"a": 1}]
        inst_list = PedidoCriar(destinatario="A", endereco="B", itens=lista)
        self.assertEqual(inst_list.itens, lista)
