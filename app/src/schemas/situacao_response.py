from pydantic import BaseModel


class SituacaoResponse(BaseModel):
    pedido_id: int
    situacao: str
