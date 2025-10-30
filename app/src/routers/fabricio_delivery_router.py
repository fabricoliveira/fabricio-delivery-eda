import json
import logging

from fastapi import APIRouter, HTTPException

from app.src.schemas.evento_ler import EventoLer
from app.src.schemas.pedido_criar import PedidoCriar
from app.src.schemas.pedido_ler import PedidoLer
from app.src.services.database_service import criar_pedido_com_outbox, obter_pedido, obter_eventos_por_pedido
from app.src.services.worker_service import enfileirar_pedido

router = APIRouter(prefix='/fabricio-delivery')


@router.post("/pedidos", response_model=PedidoLer)
def criar_pedido(payload: PedidoCriar):
    try:
        pedido = criar_pedido_com_outbox(payload.destinatario, payload.endereco, payload.itens)
        enfileirar_pedido(pedido.id)
        itens = json.loads(pedido.itens or "[]")
        return PedidoLer(id=pedido.id, destinatario=pedido.destinatario, endereco=pedido.endereco, itens=itens,
                         status=pedido.status, criado_em=pedido.criado_em)
    except Exception:
        logging.exception("Erro ao criar pedido")
        raise HTTPException(status_code=500, detail="Erro interno")


@router.get("/pedidos/{pedido_id}", response_model=PedidoLer)
def buscar_pedido(pedido_id: int):
    pedido = obter_pedido(pedido_id)
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    import json as _j
    itens = _j.loads(pedido.itens or "[]")
    return PedidoLer(id=pedido.id, destinatario=pedido.destinatario, endereco=pedido.endereco, itens=itens,
                     status=pedido.status, criado_em=pedido.criado_em)


@router.get("/pedidos/{pedido_id}/eventos", response_model=list[EventoLer])
def consultar_eventos(pedido_id: int):
    eventos = obter_eventos_por_pedido(pedido_id)
    result = []
    for e in eventos:
        result.append(EventoLer(id=str(e.id), pedido_id=int(e.pedido_id), tipo_evento=e.tipo_evento, payload=e.payload,
                                criado_em=e.criado_em))
    return result
