import json
import logging
from datetime import datetime
from time import sleep
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy.orm import Session

from app.src.configurations.database_config import SessionLocal, engine, Base
from app.src.models.evento import Evento
from app.src.models.outbox import Outbox
from app.src.models.pedido import Pedido

logger = logging.getLogger("entrega.database_service")

DB_PRONTO = False


def inicializar_db(tentativas: int = 6, backoff_segundos: float = 2.0) -> bool:
    global DB_PRONTO
    attempt = 0
    while attempt < tentativas:
        try:
            Base.metadata.create_all(bind=engine)
            DB_PRONTO = True
            logger.info("DB inicializado")
            return True
        except OperationalError as e:
            attempt += 1
            logger.warning("DB indisponível (tentativa %d/%d): %s", attempt, tentativas, e)
            sleep(backoff_segundos * attempt)
        except Exception:
            logger.exception("Falha ao inicializar DB")
            attempt += 1
            sleep(backoff_segundos * attempt)
    DB_PRONTO = False
    logger.error("Não foi possível inicializar o DB após tentativas")
    return False


def _db_pronto() -> bool:
    return DB_PRONTO


def criar_pedido_com_outbox(destinatario: str, endereco: str, itens: list, tipo_evento: str = "Pedido Recebido"):
    db: Session = SessionLocal()
    try:
        itens_text = json.dumps(itens, ensure_ascii=False)
        with db.begin():
            pedido = Pedido(destinatario=destinatario, endereco=endereco, itens=itens_text, status="recebido",
                            criado_em=datetime.utcnow())
            db.add(pedido)
            db.flush()
            out = Outbox(pedido_id=pedido.id, tipo_evento=tipo_evento,
                         payload=json.dumps({"pedido_id": pedido.id, "status": "recebido"}, ensure_ascii=False))
            db.add(out)
        db.refresh(pedido)
        return pedido
    finally:
        db.close()


def obter_pedido(pedido_id: int) -> Optional[Pedido]:
    if not _db_pronto():
        logger.debug("obter_pedido: DB não pronto")
        return None
    db: Session = SessionLocal()
    try:
        return db.get(Pedido, int(pedido_id))
    finally:
        db.close()


def salvar_evento(evento_id: str, pedido_id: int, tipo_evento: str, payload: Optional[dict] = None,
                  criado_em: Optional[datetime] = None):
    if not _db_pronto():
        logger.error("salvar_evento: DB não pronto")
        raise OperationalError("DB não pronto", params=None, orig=None)
    db: Session = SessionLocal()
    if criado_em is None:
        criado_em = datetime.utcnow()
    try:
        payload_text = None
        if payload is not None:
            try:
                payload_text = json.dumps(payload, ensure_ascii=False, default=str)
            except Exception:
                payload_text = str(payload)
        ev = Evento(id=str(evento_id), pedido_id=int(pedido_id), tipo_evento=tipo_evento, payload=payload_text,
                    criado_em=criado_em)
        with db.begin():
            db.add(ev)
        return ev
    except IntegrityError:
        logger.info("Evento já existe, ignorando id=%s", evento_id)
        return db.get(Evento, evento_id)
    finally:
        db.close()


def obter_eventos_por_pedido(pedido_id: int) -> List[Evento]:
    if not _db_pronto():
        logger.debug("obter_eventos_por_pedido: DB não pronto")
        return []
    db: Session = SessionLocal()
    try:
        stmt = select(Evento).where(Evento.pedido_id == int(pedido_id)).order_by(
            Evento.criado_em)
        return [r[0] for r in db.execute(stmt).all()]
    except OperationalError:
        logger.warning("Erro operacional ao consultar eventos")
        return []
    finally:
        db.close()


def obter_eventos_outbox_pendentes(limit: int = 100) -> List[Outbox]:
    if not _db_pronto():
        logger.debug("obter_eventos_outbox_pendentes: DB não pronto")
        return []
    db: Session = SessionLocal()
    try:
        stmt = select(Outbox).where(Outbox.publicado == False).order_by(Outbox.criado_em).limit(
            limit)
        return [r[0] for r in db.execute(stmt).all()]
    except OperationalError:
        logger.warning("Tabela outbox ausente ou erro operacional")
        global DB_PRONTO
        DB_PRONTO = False
        return []
    finally:
        db.close()


def marcar_outbox_como_publicado(outbox_id, publicado_em: Optional[datetime] = None) -> bool:
    if not _db_pronto():
        logger.debug("marcar_outbox_como_publicado: DB não pronto")
        return False
    db: Session = SessionLocal()
    if publicado_em is None:
        publicado_em = datetime.utcnow()
    try:
        with db.begin():
            item = db.get(Outbox, outbox_id)
            if not item:
                return False
            item.publicado = True
            item.publicado_em = publicado_em
            db.add(item)
        return True
    except Exception:
        logger.exception("Falha ao marcar outbox como publicado")
        return False
    finally:
        db.close()


def atualizar_status_pedido(pedido_id: int, novo_status: str) -> bool:
    if not _db_pronto():
        logger.debug("atualizar_status_pedido: DB não pronto")
        return False
    db: Session = SessionLocal()
    try:
        with db.begin():
            p = db.get(Pedido, int(pedido_id))
            if not p:
                return False
            p.status = novo_status
            db.add(p)
        return True
    except Exception:
        logger.exception("Falha ao atualizar status do pedido %s", pedido_id)
        return False
    finally:
        db.close()
