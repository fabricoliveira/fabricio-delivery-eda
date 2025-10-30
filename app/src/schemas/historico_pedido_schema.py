from pydantic import BaseModel


class HistoricoPedidoSchema(BaseModel):
    situacao: str
    timestamp: str
