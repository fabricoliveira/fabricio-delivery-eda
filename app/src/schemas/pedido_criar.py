from typing import List, Optional

from pydantic import BaseModel


class PedidoCriar(BaseModel):
    destinatario: str
    endereco: str
    itens: Optional[List[dict]] = []
