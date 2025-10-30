import logging

from app.src.enums.situacao import Situacao
from app.src.models.pedido import Pedido
from app.src.services.database_service import get_by_id, update
from app.src.usecases.criar_historico_usecase import criar_historico
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)


def _is_permitido_atualizar_situacao(situacao_pedido: Situacao, situacao_pedido_dto: Situacao) -> bool:
    if situacao_pedido.value == Situacao.PEDIDO_CANCELADO:
        logger.info(
            {
                'METHOD': 'atualizar_situacao_pedido_usecase.atualizar_situacao_pedido',
                'TIMESTAMP': time_now(),
                'EVENT': 'Não é possível alterar a situação de um pedido cancelado',
            }
        )
        return False
    if situacao_pedido_dto.value < situacao_pedido.value:
        logger.info(
            {
                'METHOD': 'atualizar_situacao_pedido_usecase.atualizar_situacao_pedido',
                'TIMESTAMP': time_now(),
                'EVENT': 'Não é possível regredir a situação do pedido',
            }
        )
        return False

    return True


def atualizar_situacao_pedido(situacao_pedido_dto: dict) -> dict:
    try:
        situacao_pedido_dto = situacao_pedido_dto.get('event')

        pedido = get_by_id(Pedido, situacao_pedido_dto.get('pedido_id'))

        if not pedido:
            logger.info(
                {
                    'METHOD': 'atualizar_situacao_pedido_usecase.atualizar_situacao_pedido',
                    'TIMESTAMP': time_now(),
                    'EVENT': 'O pedido não existe no banco de dados',
                    'PAYLOAD': situacao_pedido_dto
                }
            )
            return situacao_pedido_dto

        situacao_pedido = Situacao(pedido.get('situacao'))
        situacao_pedido_dto = Situacao(situacao_pedido_dto.get('situacao'))

        if not _is_permitido_atualizar_situacao(situacao_pedido, situacao_pedido_dto):
            return pedido
        else:
            pedido['situacao'] = situacao_pedido_dto

        pedido = Pedido(**pedido)
        pedido_dto = update(pedido)

        criar_historico(pedido_dto)

        return pedido_dto
    except Exception as e:
        raise e
