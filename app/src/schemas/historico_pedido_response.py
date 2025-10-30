from typing import List

from pydantic import BaseModel

from app.src.schemas.historico_pedido_schema import HistoricoPedidoSchema


class HistoricoPedidoResponse(BaseModel):
    pedido_id: int
    historico: List[HistoricoPedidoSchema]
