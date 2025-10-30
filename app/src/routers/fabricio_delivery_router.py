import json
import logging
from http import HTTPStatus

from fastapi import APIRouter

from app.src.configurations.settings_config import settings
from app.src.enums.situacao import Situacao
from app.src.schemas.event_schema import EventSchema
from app.src.schemas.historico_pedido_response import HistoricoPedidoResponse
from app.src.schemas.historico_pedido_schema import HistoricoPedidoSchema
from app.src.schemas.message_response import MessageResponse
from app.src.schemas.pedido_request import PedidoRequest
from app.src.schemas.situacao_request import SituacaoRequest
from app.src.schemas.situacao_response import SituacaoResponse
from app.src.services.queue_producer_service import publish_message
from app.src.usecases import consultar_situacao_pedido_usecase, consultar_historico_pedido_usecase
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)

router = APIRouter(prefix='/fabricio-delivery')


@router.post('/criar-pedido', response_model=MessageResponse, status_code=HTTPStatus.CREATED)
async def criar_pedido(pedido_request: PedidoRequest):
    pedido_request.situacao = Situacao.PEDIDO_RECEBIDO
    payload = json.loads(pedido_request.model_dump_json().encode())

    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.criar_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': f'Recebido evento de criação de pedido, publicando na fila {settings.RABBITMQ_QUEUE}.',
            'PAYLOAD': payload
        }
    )

    event = EventSchema(
        method='INSERT',
        event=payload,
        timestamp=time_now()
    )

    await publish_message(event)

    response = MessageResponse(
        status='success',
        message='Pedido adicionado com sucesso na fila para criação!'
    )

    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.criar_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': f'Finalizado a publicação na fila {settings.RABBITMQ_QUEUE} de evento de criação de pedido.',
            'PAYLOAD': payload
        }
    )

    return response


@router.patch('/atualizar-situacao-pedido/{pedido_id}', response_model=MessageResponse, status_code=HTTPStatus.OK)
async def atualizar_situacao_pedido(pedido_id: int, situacao_request: SituacaoRequest):
    situacao_request.pedido_id = pedido_id
    payload = json.loads(situacao_request.model_dump_json().encode())

    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.atualizar_situacao_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': f'Recebido evento de atualização de pedido, publicando na fila {settings.RABBITMQ_QUEUE}.',
            'PAYLOAD': payload
        }
    )

    event = EventSchema(
        method='UPDATE',
        event=payload,
        timestamp=time_now()
    )

    await publish_message(event)

    response = MessageResponse(
        status='success',
        message='Situação do pedido adicionado com sucesso na fila para atualização!'
    )

    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.atualizar_situacao_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': f'Finalizado a publicação na fila {settings.RABBITMQ_QUEUE} de evento de atualização de pedido',
            'PAYLOAD': payload
        }
    )

    return response


@router.get('/consultar-situacao-pedido/{pedido_id}', response_model=SituacaoResponse, status_code=HTTPStatus.OK)
async def consultar_situacao_pedido(pedido_id: int):
    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.consultar_situacao_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': 'Recebido evento de consulta de situação de pedido.',
            'PEDIDO_ID': pedido_id
        }
    )

    response = consultar_situacao_pedido_usecase.consultar_situacao_pedido(pedido_id)
    situacao_response = SituacaoResponse(
        pedido_id=pedido_id,
        situacao=Situacao(response.get('situacao')).name if response else 'PEDIDO_NAO_ENCONTRADO'
    )

    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.consultar_situacao_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': 'Finalizado evento de consulta de situação de pedido.',
            'PAYLOAD': response
        }
    )

    return situacao_response


@router.get('/consultar-historico-pedido/{pedido_id}', response_model=HistoricoPedidoResponse,
            status_code=HTTPStatus.OK)
async def consultar_historico_pedido(pedido_id: int):
    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.consultar_historico_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': 'Recebido evento de consulta de histórico de pedido.',
            'PEDIDO_ID': pedido_id
        }
    )

    response = consultar_historico_pedido_usecase.consultar_historico_pedido(pedido_id)
    historico_response = HistoricoPedidoResponse(pedido_id=pedido_id, historico=[])
    for r in response:
        historico_response.historico.append(
            HistoricoPedidoSchema(
                situacao=Situacao(r.get('situacao')).name,
                timestamp=r.get('timestamp')
            )
        )

    logger.info(
        {
            'METHOD': 'fabricio_delivery_router.consultar_situacao_pedido',
            'TIMESTAMP': time_now(),
            'EVENT': 'Finalizado evento de consulta de situação de pedido.',
            'PAYLOAD': response
        }
    )
    return historico_response
