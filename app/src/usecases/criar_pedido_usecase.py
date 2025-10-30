import logging

from app.src.enums.situacao import Situacao
from app.src.models.pedido import Pedido
from app.src.services.database_service import insert, get_by_id
from app.src.usecases.criar_historico_usecase import criar_historico
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)


def criar_pedido(pedido_dto: dict) -> dict:
    try:
        logger.info(
            {
                'METHOD': 'criar_pedido_usecase.criar_pedido',
                'TIMESTAMP': time_now(),
                'EVENT': 'Criando um novo pedido',
                'PAYLOAD': pedido_dto
            }
        )

        pedido_dto = pedido_dto.get('event')

        if get_by_id(Pedido, pedido_dto.get('pedido_id')):
            logger.info(
                {
                    'METHOD': 'criar_pedido_usecase.criar_pedido',
                    'TIMESTAMP': time_now(),
                    'EVENT': 'O pedido já existe no banco de dados',
                    'PAYLOAD': pedido_dto
                }
            )
            return pedido_dto

        pedido_dto['situacao'] = Situacao(pedido_dto.get('situacao'))
        pedido = insert(pedido_dto)

        criar_historico(pedido_dto)

        return pedido_dto
    except Exception as e:
        raise e
