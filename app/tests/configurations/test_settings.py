import importlib
import unittest
from unittest.mock import patch

MODULE_PATH = "app.src.configurations.settings"


def _carregar_settings_com_env(mapping: dict):
    with patch("dotenv.load_dotenv") as _ld, patch("os.getenv") as getenv_mock:
        getenv_mock.side_effect = lambda key, default=None: mapping.get(key, default)
        module = importlib.import_module(MODULE_PATH)
        importlib.reload(module)
        return module.settings


class TestSettings(unittest.TestCase):
    def test_postgres_url_default(self):
        settings = _carregar_settings_com_env({})
        expected = "postgresql+psycopg2://postgres:1234@localhost:5432/fabricio_delivery_db"
        self.assertEqual(settings.POSTGRES_URL, expected)

    def test_postgres_url_custom_values(self):
        mapping = {
            "POSTGRES_USER": "u1",
            "POSTGRES_PASSWORD": "p1",
            "POSTGRES_HOST": "dbhost",
            "POSTGRES_PORT": "6543",
            "POSTGRES_DB": "minhadb",
        }
        settings = _carregar_settings_com_env(mapping)
        expected = "postgresql+psycopg2://u1:p1@dbhost:6543/minhadb"
        self.assertEqual(settings.POSTGRES_URL, expected)

    def test_rabbitmq_url_default(self):
        settings = _carregar_settings_com_env({})
        expected = "amqp://rabbitmq:1234@localhost:5672/"
        self.assertEqual(settings.RABBITMQ_URL, expected)

    def test_rabbitmq_url_custom_values(self):
        mapping = {
            "RABBITMQ_USER": "rmq_user",
            "RABBITMQ_PW": "rmq_pw",
            "RABBITMQ_HOST": "rmq_host",
            "RABBITMQ_PORT": "5678",
        }
        settings = _carregar_settings_com_env(mapping)
        expected = "amqp://rmq_user:rmq_pw@rmq_host:5678/"
        self.assertEqual(settings.RABBITMQ_URL, expected)

    def test_config_env_file(self):
        settings = _carregar_settings_com_env({})
        self.assertTrue(hasattr(settings, "Config"))
        config = settings.Config
        self.assertEqual(getattr(config, "env_file", None), ".env")
