import logging

from app.src.models.historico_pedido import HistoricoPedido
from app.src.services.database_service import insert
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)


def criar_historico(dto: dict) -> dict:
    try:
        historico = HistoricoPedido(
            pedido_id=dto.get('pedido_id'),
            situacao=dto.get('situacao'),
            timestamp=time_now()
        )
        historico_dto = insert(historico)

        logger.info(
            {
                'METHOD': 'criar_historico_usecase.criar_historico',
                'TIMESTAMP': time_now(),
                'EVENT': 'Dados de historico de pedido gravados no banco de dados',
                'PAYLOAD': historico_dto
            }
        )

        return historico_dto
    except Exception as e:
        raise e
