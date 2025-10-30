from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class EventoLer(BaseModel):
    id: str
    pedido_id: int
    tipo_evento: str
    payload: Optional[str]
    criado_em: datetime

    model_config = {"from_attributes": True}
