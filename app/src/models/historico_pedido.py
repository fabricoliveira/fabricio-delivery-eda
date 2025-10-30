from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from app.src.enums.situacao import Situacao


class HistoricoPedido(SQLModel, table=True):
    __tablename__ = 'tb_historico_pedidos'

    id: Optional[int] = Field(default=None, primary_key=True)
    pedido_id: int
    situacao: Situacao
    timestamp: str

    pedido_id: Optional[int] = Field(default=None, foreign_key='tb_pedidos.pedido_id')
    pedido: Optional['Pedido'] = Relationship(back_populates='historicos')
