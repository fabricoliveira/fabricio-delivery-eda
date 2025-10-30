from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.src.enums.situacao import Situacao


class Pedido(SQLModel, table=True):
    __tablename__ = 'tb_pedidos'

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int = Field(index=True, unique=True)
    nome_cliente: str = Field(min_length=3, max_length=50)
    cep: str = Field(min_length=8, max_length=9)
    item: str = Field(min_length=3, max_length=50)
    situacao: Situacao = Field(default=Situacao.PEDIDO_RECEBIDO)

    historicos: Optional['HistoricoPedido'] = Relationship(back_populates='pedido')
