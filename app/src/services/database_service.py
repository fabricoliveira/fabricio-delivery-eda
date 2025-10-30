import asyncio
import logging

from sqlalchemy.exc import OperationalError
from sqlmodel import SQLModel, create_engine, Session, select

from app.src.configurations.settings_config import settings
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.POSTGRES_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={'connect_timeout': 10}
)


async def wait_for_db(retries: int = 5, delay: float = 1.0, backoff: float = 1.2):
    logging.getLogger().setLevel(logging.INFO)
    current_delay = delay
    for tentativa in range(1, retries + 1):
        try:
            with engine.connect() as conn:
                logger.info(
                    {
                        'METHOD': 'database_service.wait_for_db',
                        'TIMESTAMP': time_now(),
                        'EVENT': f'Conectado ao banco de dados tentativa {tentativa}/{retries}.'
                    }
                )
                return
        except OperationalError as exc:
            logger.warning(
                {
                    'METHOD': 'database_service.wait_for_db',
                    'TIMESTAMP': time_now(),
                    'EVENT': f'Banco indisponível, tentativa {tentativa}/{retries} : {exc}'
                }
            )
        except Exception as exc:
            logger.warning(
                {
                    'METHOD': 'database_service.wait_for_db',
                    'TIMESTAMP': time_now(),
                    'EVENT': f'Erro de conexão ao DB  {tentativa}/{retries} : {exc}'
                }
            )

        await asyncio.sleep(current_delay)
        current_delay *= backoff

    raise RuntimeError('Banco de dados indisponível após tentativas')


def insert(model_instance: SQLModel) -> dict:
    try:
        with Session(engine) as session:
            session.add(model_instance)
            session.commit()
            session.refresh(model_instance)
            return model_instance.model_dump()
    except Exception as e:
        logger.error(
            {
                'METHOD': 'database_service.wait_for_db',
                'TIMESTAMP': time_now(),
                'EVENT': f'Erro ao inserir dados: {e}'
            }
        )
        raise e


def update(model_instance: SQLModel) -> dict:
    try:
        with Session(engine) as session:
            persisted = session.merge(model_instance)
            session.commit()
            session.refresh(persisted)
            return persisted.model_dump()
    except Exception as e:
        logger.error(
            {
                'METHOD': 'database_service.wait_for_db',
                'TIMESTAMP': time_now(),
                'EVENT': f'Erro ao atualizar dados: {e}'
            }
        )
        raise e


def get_by_id(model_class: type[SQLModel], pedido_id: int) -> dict:
    try:
        with Session(engine) as session:
            statement = select(model_class).where(model_class.pedido_id == pedido_id)
            result = session.exec(statement).first()
            return result.model_dump() if result else {}
    except Exception as e:
        logger.error(
            {
                'METHOD': 'database_service.wait_for_db',
                'TIMESTAMP': time_now(),
                'EVENT': f'Erro ao buscar dados por ID: {e}'
            }
        )
        raise e


def findall_by_id(model_class: type[SQLModel], pedido_id: int) -> list[dict]:
    try:
        with Session(engine) as session:
            statement = select(model_class).where(model_class.pedido_id == pedido_id)
            results = session.exec(statement).all()
            return [result.model_dump() for result in results] if results else []
    except Exception as e:
        logger.error(
            {
                'METHOD': 'database_service.wait_for_db',
                'TIMESTAMP': time_now(),
                'EVENT': f'Erro ao buscar todos os dados por ID: {e}'
            }
        )
        raise e
