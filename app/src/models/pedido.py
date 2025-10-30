from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime

from app.src.configurations.database_config import Base


class Pedido(Base):
    __tablename__ = "pedidos"
    id = Column(Integer, primary_key=True, index=True)
    destinatario = Column(String(255), nullable=False)
    endereco = Column(Text, nullable=False)
    itens = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, index=True, default="recebido")
    criado_em = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    atualizado_em = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
