import asyncio
import json
import logging

import aio_pika

from app.src.configurations.settings_config import settings
from app.src.schemas.event_schema import EventSchema
from app.src.utils.utils import time_now

logger = logging.getLogger(__name__)


async def publish_message(message: EventSchema, retries: int = 5, initial_delay: float = 1.0) -> None:
    delay = initial_delay

    for tentativa in range(1, retries + 1):
        try:
            logger.info({
                'METHOD': 'queue_producer.publish_message',
                'TIMESTAMP': time_now(),
                'EVENT': f'Tentando conectar na fila {settings.RABBITMQ_QUEUE}'
            })

            connection = await aio_pika.connect_robust(
                f'amqp://{settings.RABBITMQ_USER}:{settings.RABBITMQ_PW}@{settings.RABBITMQ_HOST}:{settings.RABBITMQ_PORT}/'
            )
            async with connection:
                channel = await connection.channel()
                queue = await channel.declare_queue(settings.RABBITMQ_QUEUE, durable=True)

                msg = aio_pika.Message(
                    body=json.dumps(message.model_dump()).encode(),
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                )

                logger.info({
                    'METHOD': 'queue_producer.publish_message',
                    'TIMESTAMP': time_now(),
                    'EVENT': f"Publicando mensagem na fila '{settings.RABBITMQ_QUEUE}'"
                })

                await channel.default_exchange.publish(
                    msg,
                    routing_key=queue.name
                )
                return
        except Exception as e:
            if tentativa == retries:
                logger.exception({
                    'METHOD': 'queue_consumer.main',
                    'TIMESTAMP': time_now(),
                    'EVENT': f'Erro ao publicar mensagem após {retries} tentativas.',
                    'EXCEPTION': e
                })
                raise e

            logger.exception({
                'METHOD': 'queue_consumer.main',
                'TIMESTAMP': time_now(),
                'EVENT': f'Tentativa {tentativa} falhou: {e}. Re-tentando em {delay}s...',
                'EXCEPTION': e
            })
            await asyncio.sleep(delay)
            delay *= 2
