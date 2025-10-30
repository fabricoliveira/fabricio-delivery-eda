import asyncio
import json
import logging
from datetime import datetime

import aio_pika
import aiormq.exceptions as amqp_exceptions

from app.src.configurations.settings import settings
from app.src.services.database_service import atualizar_status_pedido, salvar_evento

logger = logging.getLogger("entrega.consumer_service")
AMQP_URL = settings.RABBITMQ_URL
RABBIT_EXCHANGE = "entrega-exchange"
RABBIT_QUEUE = settings.RABBITMQ_QUEUE


async def iniciar_consumidor(backoff_inicial: float = 1.0, backoff_max: float = 30.0):
    backoff = backoff_inicial
    while True:
        try:
            logger.info("Tentando conectar ao broker %s", AMQP_URL)
            connection = await aio_pika.connect_robust(AMQP_URL)
            async with connection:
                channel = await connection.channel()
                exchange = await channel.declare_exchange(RABBIT_EXCHANGE, aio_pika.ExchangeType.FANOUT, durable=True)
                queue = await channel.declare_queue(RABBIT_QUEUE, durable=True)
                await queue.bind(exchange)
                backoff = backoff_inicial
                async with queue.iterator() as iterator:
                    async for message in iterator:
                        async with message.process():
                            try:
                                corpo = message.body.decode("utf-8")
                                try:
                                    obj = json.loads(corpo)
                                except Exception:
                                    obj = {"raw": corpo}
                                pedido_id = obj.get("pedido_id")
                                tipo = obj.get("status") or obj.get("tipo_evento") or "evento"
                                evento_id = obj.get("id") or f"{pedido_id}-{int(datetime.utcnow().timestamp() * 1000)}"
                                await asyncio.to_thread(salvar_evento, str(evento_id), pedido_id, tipo, obj,
                                                        datetime.utcnow())
                                await asyncio.to_thread(atualizar_status_pedido, pedido_id,
                                                        tipo if tipo in ("separacao", "em_transporte", "entregue",
                                                                         "Pedido em separação", "Pedido em transporte",
                                                                         "Pedido entregue") else tipo)
                                logger.info("Consumidor persistiu evento %s para pedido %s", evento_id, pedido_id)
                            except Exception:
                                logger.exception("Erro ao processar mensagem do broker")
        except asyncio.CancelledError:
            logger.info("Consumidor cancelado")
            raise
        except (amqp_exceptions.AMQPConnectionError, ConnectionRefusedError, OSError) as e:
            logger.warning("Falha de conexão AMQP: %s — reconectando em %.1fs", e, backoff)
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, backoff_max)
            continue
        except Exception:
            logger.exception("Erro inesperado no consumidor; reconectando")
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, backoff_max)
            continue
