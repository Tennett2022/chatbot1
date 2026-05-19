from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    channel = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    message_count = Column(Integer, default=0)
    metadata_ = Column("metadata", JSON, nullable=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    channel = Column(String, nullable=False)
    message_in = Column(Text, nullable=False)
    message_out = Column(Text, nullable=False)
    intent = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    escalated = Column(Boolean, default=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata_ = Column("metadata", JSON, nullable=True)


class Lead(Base):
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    channel = Column(String, nullable=False)
    nombre = Column(String, nullable=True)
    empresa = Column(String, nullable=True)
    rubro = Column(String, nullable=True)
    cargo = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefono = Column(String, nullable=True)
    canal_preferido = Column(String, nullable=True)
    problema_principal = Column(Text, nullable=True)
    servicio_interesado = Column(String, nullable=True)
    presupuesto_estimado = Column(String, nullable=True)
    urgencia = Column(String, nullable=True)
    mensaje_original = Column(Text, nullable=True)
    estado = Column(String, default="nuevo")
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_actualizacion = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventLog(Base):
    __tablename__ = "event_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, nullable=False)
    user_id = Column(String, nullable=True)
    channel = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    payload = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
