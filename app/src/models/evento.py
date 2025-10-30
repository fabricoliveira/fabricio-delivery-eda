from datetime import datetime

from sqlalchemy import Column, String, Integer, Text, DateTime, UniqueConstraint

from app.src.configurations.database_config import Base


class Evento(Base):
    __tablename__ = "eventos"
    id = Column(String(128), primary_key=True, index=True)
    pedido_id = Column(Integer, nullable=False, index=True)
    tipo_evento = Column(String(128), nullable=False)
    payload = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    __table_args__ = (UniqueConstraint('id', name='uq_evento_id'),)
