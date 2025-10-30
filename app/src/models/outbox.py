import uuid
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID

from app.src.configurations.database_config import Base


class Outbox(Base):
    __tablename__ = "outbox"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pedido_id = Column(Integer, nullable=False, index=True)
    tipo_evento = Column(String(128), nullable=False)
    payload = Column(Text, nullable=True)
    publicado = Column(Boolean, nullable=False, default=False, index=True)
    criado_em = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    publicado_em = Column(DateTime(timezone=True), nullable=True)
