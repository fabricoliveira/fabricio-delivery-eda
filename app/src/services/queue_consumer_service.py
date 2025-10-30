from aio_pika import DeliveryMode

from app.src.configurations.logging_config import configure_logging

configure_logging()

import asyncio
import json
import logging

import aio_pika

from app.src.configurations.settings_config import settings
from app.src.usecases.atualizar_situacao_pedido_usecase import atualizar_situacao_pedido
from app.src.usecases.criar_pedido_usecase import criar_pedido
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)


async def handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process():
        try:
            payload = json.loads(message.body.decode('utf-8'))
            logger.info(
                {
                    'METHOD': 'queue_consumer.handle_message',
                    'TIMESTAMP': time_now(),
                    'EVENT': f'Mensagem recebida na fila {settings.RABBITMQ_QUEUE}.',
                    'PAYLOAD': payload
                }
            )

            match (payload.get('method')):
                case 'INSERT':
                    criar_pedido(payload)
                case 'UPDATE':
                    atualizar_situacao_pedido(payload)

        except Exception as exc:
            logger.exception(
                {
                    'METHOD': 'queue_consumer.handle_message',
                    'TIMESTAMP': time_now(),
                    'EVENT': 'Erro ao processar mensagem',
                    'EXCEPTION': exc
                }
            )

            try:
                requeues = message.headers.get('x-requeue', 0) + 1

                if requeues >= 3:
                    logger.info({
                        'METHOD': 'queue_consumer.handle_message',
                        'TIMESTAMP': time_now(),
                        'EVENT': 'Descartando a mensagem para evitar loop infinito, após tentar processar 3 vezes.',
                        'PAYLOAD': payload

                    })
                else:
                    logger.info({
                        'METHOD': 'queue_consumer.handle_message',
                        'TIMESTAMP': time_now(),
                        'EVENT': f'Reenviando a mensagem para a fila {settings.RABBITMQ_QUEUE} para reprocessamento.',
                        'PAYLOAD': payload
                    })

                    headers = dict(message.headers or {})
                    headers['x-requeue'] = requeues
                    requeue_message = aio_pika.Message(
                        body=json.dumps(payload).encode(),
                        headers=headers,
                        delivery_mode=DeliveryMode.PERSISTENT,
                    )

                    connection = await aio_pika.connect_robust(
                        f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PW}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/'
                    )
                    async with connection:
                        channel = await connection.channel()
                        await channel.default_exchange.publish(
                            requeue_message,
                            routing_key=settings.RABBITMQ_QUEUE
                        )

            except Exception as e:
                logger.exception({
                    'METHOD': 'queue_consumer.handle_message',
                    'TIMESTAMP': time_now(),
                    'EVENT': 'Falha ao republicar/registrar; descartando mensagem para evitar loop infinito',
                    'EXCEPTION': e
                })


async def _connect_and_consume(stop_event: asyncio.Event) -> None:
    url = f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PW}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/'
    backoff = 1.0

    while not stop_event.is_set():
        try:
            logger.info({
                'METHOD': 'queue_consumer.connect_and_consume',
                'TIMESTAMP': time_now(),
                'EVENT': f'Tentando conectar na fila {settings.RABBITMQ_QUEUE}'
            })

            connection = await aio_pika.connect_robust(url)

            async with connection:
                channel = await connection.channel()
                await channel.set_qos(prefetch_count=1)
                queue = await channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True)
                logger.info({
                    'METHOD': 'queue_consumer.connect_and_consume',
                    'TIMESTAMP': time_now(),
                    'EVENT': f"Consumindo da fila '{settings.RABBITMQ_QUEUE}'"
                })
                await queue.consume(handle_message)
                await stop_event.wait()
                return
        except Exception as exc:
            logger.warning({
                'METHOD': 'queue_consumer.connect_and_consume',
                'TIMESTAMP': time_now(),
                'EVENT': f'Falha ao conectar/consumir: {exc}. Re-tentando em {backoff}s'
            })
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)


if __name__ == '__main__':
    logger.info({
        'METHOD': 'queue_consumer.main',
        'TIMESTAMP': time_now(),
        'EVENT': f'Inicializando o listener da fila {settings.RABBITMQ_QUEUE}.'
    })

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    stop_event = asyncio.Event()

    consumer_task = loop.create_task(_connect_and_consume(stop_event))

    try:
        loop.run_until_complete(stop_event.wait())
    finally:
        stop_event.set()
        loop.run_until_complete(asyncio.gather(consumer_task, return_exceptions=True))
        loop.close()

        logger.info({
            'METHOD': 'queue_consumer.main',
            'TIMESTAMP': time_now(),
            'EVENT': f'Listener da fila {settings.RABBITMQ_QUEUE} finalizado.'
        })
