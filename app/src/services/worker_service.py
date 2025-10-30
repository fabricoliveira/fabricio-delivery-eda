import asyncio
import json
import logging
from datetime import datetime

from app.src.configurations.database_config import SessionLocal
from app.src.models.outbox import Outbox
from app.src.services.database_service import atualizar_status_pedido

logger = logging.getLogger("entrega.worker_service")
logger.setLevel(logging.INFO)

pedido_queue: asyncio.Queue = asyncio.Queue()


def enfileirar_pedido(pedido_id: int):
    try:
        pedido_queue.put_nowait(pedido_id)
        logger.info("Pedido %s enfileirado para processamento", pedido_id)
    except Exception:
        logger.exception("Falha ao enfileirar pedido %s", pedido_id)


async def processar_pedidos_loop():
    passos = [
        ("separacao", "Pedido em separação"),
        ("em_transporte", "Pedido em transporte"),
        ("entregue", "Pedido entregue"),
    ]

    logger.info("Loop de processamento de pedidos iniciado")
    while True:
        try:
            try:
                pid = await asyncio.wait_for(pedido_queue.get(), timeout=2.0)
            except asyncio.TimeoutError:
                pid = None

            if pid is None:
                await asyncio.sleep(0.5)
                continue

            logger.info("Processando pedido %s: iniciando fluxo de entrega", pid)

            for status, descricao in passos:
                etapa_inicio = datetime.utcnow()
                logger.info("Pedido %s: iniciando etapa '%s' (%s) — %s", pid, status, descricao,
                            etapa_inicio.isoformat())

                def cria_outbox_e_retorna_id():
                    db = SessionLocal()
                    try:
                        payload = {"pedido_id": pid, "status": status, "timestamp": datetime.utcnow().isoformat()}
                        out = Outbox(pedido_id=pid, tipo_evento=descricao,
                                     payload=json.dumps(payload, ensure_ascii=False))
                        with db.begin():
                            db.add(out)
                            db.flush()
                            out_id = out.id
                        return str(out_id)
                    finally:
                        db.close()

                try:
                    outbox_id = await asyncio.to_thread(cria_outbox_e_retorna_id)
                    logger.info("Pedido %s: outbox criado id=%s status=%s", pid, outbox_id, status)
                except Exception:
                    logger.exception("Pedido %s: erro ao criar outbox para status %s", pid, status)

                try:
                    updated = await asyncio.to_thread(atualizar_status_pedido, pid, status)
                    if updated:
                        logger.info("Pedido %s: status atualizado para '%s'", pid, status)
                    else:
                        logger.warning("Pedido %s: não foi possível atualizar status para '%s' (pedido inexistente?)",
                                       pid, status)
                except Exception:
                    logger.exception("Pedido %s: exceção ao atualizar status para %s", pid, status)

                duracao = (datetime.utcnow() - etapa_inicio).total_seconds()
                logger.info("Pedido %s: etapa '%s' concluída em %.3fs", pid, status, duracao)

                await asyncio.sleep(1.0)

            logger.info("Processamento do pedido %s concluído", pid)

        except Exception:
            logger.exception("Erro no loop de processamento de pedidos; aguardando antes de continuar")
            await asyncio.sleep(5)
