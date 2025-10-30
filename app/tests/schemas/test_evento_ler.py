import importlib
import unittest
from datetime import datetime
from types import SimpleNamespace

MODULE = "app.src.schemas.evento_ler"


class TestEventoLerSchema(unittest.TestCase):
    def _load_model(self):
        mod = importlib.import_module(MODULE)
        importlib.reload(mod)
        return mod.EventoLer

    def test_model_config_from_attributes_enabled(self):
        EventoLer = self._load_model()
        cfg = getattr(EventoLer, "model_config", {})
        self.assertTrue(cfg.get("from_attributes", False), "model_config deve ter from_attributes=True")

    def test_instantiation_from_dict_and_field_types(self):
        EventoLer = self._load_model()
        now = datetime.utcnow()
        data = {
            "id": "evt-1",
            "pedido_id": 123,
            "tipo_evento": "created",
            "payload": None,
            "criado_em": now,
        }
        obj = EventoLer(**data)
        self.assertEqual(obj.id, data["id"])
        self.assertEqual(obj.pedido_id, data["pedido_id"])
        self.assertEqual(obj.tipo_evento, data["tipo_evento"])
        self.assertIsNone(obj.payload)
        self.assertIsInstance(obj.criado_em, datetime)
        self.assertAlmostEqual(obj.criado_em.timestamp(), now.timestamp(), delta=1)

    def test_instantiation_parses_iso_datetime_string(self):
        EventoLer = self._load_model()
        now = datetime.utcnow().replace(microsecond=0)
        data = {
            "id": "evt-iso",
            "pedido_id": 1,
            "tipo_evento": "updated",
            "payload": "{}",
            "criado_em": now.isoformat(),
        }
        obj = EventoLer(**data)
        self.assertIsInstance(obj.criado_em, datetime)
        self.assertEqual(obj.criado_em.replace(microsecond=0), now)

    def test_model_validate_from_attributes_with_mock_object(self):
        EventoLer = self._load_model()
        now = datetime.utcnow()
        fake = SimpleNamespace(
            id="evt-mock",
            pedido_id=42,
            tipo_evento="mocked",
            payload="{\"a\":1}",
            criado_em=now.isoformat(),
        )

        model_validate = getattr(EventoLer, "model_validate", None)
        if callable(model_validate):
            inst = EventoLer.model_validate(fake)
        else:
            attrs = {k: getattr(fake, k) for k in ("id", "pedido_id", "tipo_evento", "payload", "criado_em")}
            inst = EventoLer(**attrs)

        self.assertEqual(inst.id, fake.id)
        self.assertEqual(inst.pedido_id, fake.pedido_id)
        self.assertEqual(inst.tipo_evento, fake.tipo_evento)
        self.assertEqual(inst.payload, fake.payload)
        self.assertIsInstance(inst.criado_em, datetime)
