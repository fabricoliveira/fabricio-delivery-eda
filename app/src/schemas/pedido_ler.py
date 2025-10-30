from datetime import datetime
from typing import List

from pydantic import BaseModel


class PedidoLer(BaseModel):
    id: int
    destinatario: str
    endereco: str
    itens: List[dict]
    status: str
    criado_em: datetime

    model_config = {"from_attributes": True}
