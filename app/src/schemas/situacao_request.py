from typing import Optional

from pydantic import BaseModel

from app.src.enums.situacao import Situacao


class SituacaoRequest(BaseModel):
    pedido_id: Optional[int] = None
    situacao: Situacao
