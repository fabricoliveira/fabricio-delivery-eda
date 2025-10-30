import importlib
import unittest
from types import SimpleNamespace
from unittest.mock import patch, MagicMock


class TestDatabaseConfig(unittest.TestCase):
    def _reload_mod_com_mocks(self, postgres_url="postgresql://user:pass@host:5432/db"):
        mocks = {}
        settings_target = 'app.src.configurations.settings.settings'
        module_target = 'app.src.configurations.database_config'

        cm_create_engine = patch('sqlalchemy.create_engine')
        cm_sessionmaker = patch('sqlalchemy.orm.sessionmaker')
        cm_declarative = patch('sqlalchemy.orm.declarative_base')
        cm_settings = patch(settings_target, new=SimpleNamespace(POSTGRES_URL=postgres_url))

        create_engine_mock = cm_create_engine.start()
        sessionmaker_mock = cm_sessionmaker.start()
        declarative_mock = cm_declarative.start()
        cm_settings.start()

        create_engine_mock.return_value = MagicMock(name="engine_obj")
        sessionmaker_mock.return_value = MagicMock(name="SessionLocal_obj")
        declarative_mock.return_value = MagicMock(name="Base_obj")

        module = importlib.import_module(module_target)
        importlib.reload(module)

        mocks['create_engine'] = create_engine_mock
        mocks['sessionmaker'] = sessionmaker_mock
        mocks['declarative_base'] = declarative_mock

        mocks['__patch_stop_list__'] = (cm_create_engine, cm_sessionmaker, cm_declarative, cm_settings)
        return module, mocks

    def _stop_mocks(self, stop_list):
        for cm in stop_list:
            cm.stop()

    def test_engine_criado_com_url_e_future(self):
        mod, mocks = self._reload_mod_com_mocks(postgres_url="postgresql://teste:5432/minhadb")
        try:
            mocks['create_engine'].assert_called()
            called_args, called_kwargs = mocks['create_engine'].call_args
            self.assertEqual(called_args[0], "postgresql://teste:5432/minhadb")
            self.assertIn('future', called_kwargs)
            self.assertTrue(called_kwargs['future'])
            self.assertIs(mod.engine, mocks['create_engine'].return_value)
        finally:
            self._stop_mocks(mocks['__patch_stop_list__'])

    def test_sessionmaker_configurado_com_engine_e_opcoes(self):
        mod, mocks = self._reload_mod_com_mocks()
        try:
            mocks['sessionmaker'].assert_called()
            called_kwargs = mocks['sessionmaker'].call_args.kwargs
            self.assertIn('bind', called_kwargs)
            self.assertIs(called_kwargs['bind'], mocks['create_engine'].return_value)
            self.assertEqual(called_kwargs.get('autoflush'), False)
            self.assertEqual(called_kwargs.get('autocommit'), False)
            self.assertEqual(called_kwargs.get('future'), True)
            self.assertIs(mod.SessionLocal, mocks['sessionmaker'].return_value)
        finally:
            self._stop_mocks(mocks['__patch_stop_list__'])

    def test_base_e_declarative_base(self):
        mod, mocks = self._reload_mod_com_mocks()
        try:
            mocks['declarative_base'].assert_called()
            self.assertIs(mod.Base, mocks['declarative_base'].return_value)
        finally:
            self._stop_mocks(mocks['__patch_stop_list__'])
