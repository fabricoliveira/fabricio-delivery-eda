import logging

from app.src.models.historico_pedido import HistoricoPedido
from app.src.services.database_service import findall_by_id
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)


def consultar_historico_pedido(pedido_id: int) -> list[dict]:
    historico_pedido = findall_by_id(HistoricoPedido, pedido_id)

    if not historico_pedido:
        logger.info(
            {
                'METHOD': 'consultar_historico_pedido_usecase.consultar_historico_pedido',
                'TIMESTAMP': time_now(),
                'EVENT': 'O historico do pedido não existe no banco de dados',
                'PEDIDO_ID': pedido_id
            }
        )
        return []

    return historico_pedido
