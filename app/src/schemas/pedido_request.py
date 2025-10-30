from typing import Optional

from pydantic import BaseModel, Field

from app.src.enums.situacao import Situacao


class PedidoRequest(BaseModel):
    pedido_id: int = Field(gt=0)
    nome_cliente: str = Field(min_length=3, max_length=50)
    cep: str = Field(min_length=8, max_length=9)
    item: str = Field(min_length=1, max_length=50)
    situacao: Optional[Situacao] = None
