import logging

from app.src.models.pedido import Pedido
from app.src.services.database_service import get_by_id
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)


def consultar_situacao_pedido(pedido_id: int) -> dict:
    pedido = get_by_id(Pedido, pedido_id)

    if not pedido:
        logger.info(
            {
                'METHOD': 'consultar_situacao_pedido_usecase.consultar_situacao_pedido',
                'TIMESTAMP': time_now(),
                'EVENT': 'O pedido não existe no banco de dados',
                'PEDIDO_ID': pedido_id
            }
        )
        return None

    return {
        'pedido_id': pedido_id,
        'situacao': pedido.get('situacao')
    }
