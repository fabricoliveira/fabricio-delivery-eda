import asyncio
import logging
from datetime import datetime

import aio_pika

from app.src.configurations.settings import settings
from app.src.services.database_service import obter_eventos_outbox_pendentes, marcar_outbox_como_publicado

logger = logging.getLogger("entrega.publisher_service")
AMQP_URL = settings.RABBITMQ_URL
RABBIT_EXCHANGE = "entrega-exchange"


async def publicar_outbox_loop(poll_interval: float = 1.0):
    while True:
        try:
            eventos = await asyncio.to_thread(obter_eventos_outbox_pendentes, 100)
            if not eventos:
                await asyncio.sleep(poll_interval)
                continue
            connection = await aio_pika.connect_robust(AMQP_URL)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(RABBIT_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True)
                for out in eventos:
                    try:
                        body = out.payload or ""
                        message = aio_pika.Message(body.encode("utf-8"))
                        await exchange.publish(message, routing_key="")
                        await asyncio.to_thread(marcar_outbox_como_publicado, out.id, datetime.utcnow())
                        logger.info("Outbox publicado id=%s pedido_id=%s", out.id, out.pedido_id)
                    except Exception:
                        logger.exception("Falha ao publicar outbox id=%s", out.id)
                await asyncio.sleep(0.05)
        except Exception:
            logger.exception("Erro no loop de publicação do outbox")
            await asyncio.sleep(2)
