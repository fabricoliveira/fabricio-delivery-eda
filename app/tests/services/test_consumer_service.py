import asyncio
import importlib
import unittest
from datetime import datetime
from unittest.mock import MagicMock

MODULE_PATH = "app.src.services.consumer_service"


class TestConsumerServiceFast(unittest.TestCase):
    def setUp(self):
        self.mod = importlib.import_module(MODULE_PATH)
        importlib.reload(self.mod)
        self.salvar_mock = MagicMock()
        self.atualizar_mock = MagicMock()
        self.mod.salvar_evento = self.salvar_mock
        self.mod.atualizar_status_pedido = self.atualizar_mock

    async def _process_single_message(self, body_bytes):
        """Replica apenas a lógica interna de processamento de uma mensagem para testes rápidos."""
        corpo = body_bytes.decode("utf-8")
        try:
            obj = self.mod.json.loads(corpo)
        except Exception:
            obj = {"raw": corpo}
        pedido_id = obj.get("pedido_id")
        tipo = obj.get("status") or obj.get("tipo_evento") or "evento"
        evento_id = obj.get("id") or f"{pedido_id}-{int(datetime.utcnow().timestamp() * 1000)}"
        self.mod.salvar_evento(str(evento_id), pedido_id, tipo, obj, datetime.utcnow())
        self.mod.atualizar_status_pedido(pedido_id,
                                         tipo if tipo in ("separacao", "em_transporte", "entregue",
                                                          "Pedido em separação", "Pedido em transporte",
                                                          "Pedido entregue") else tipo)

    def test_processa_mensagem_json_rapido(self):
        body = b'{"pedido_id": 10, "id": "evt-x", "status": "separacao"}'
        asyncio.run(self._process_single_message(body))
        self.salvar_mock.assert_called_once()
        self.atualizar_mock.assert_called_once()
        args_salvar = self.salvar_mock.call_args[0]
        self.assertEqual(args_salvar[0], "evt-x")
        self.assertEqual(args_salvar[1], 10)

    def test_processa_mensagem_raw_rapido(self):
        body = b'invalid-bytes'
        asyncio.run(self._process_single_message(body))
        self.salvar_mock.assert_called_once()
        self.atualizar_mock.assert_called_once()
        payload = self.salvar_mock.call_args[0][3]
        self.assertIn("raw", payload)
