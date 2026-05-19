from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.storage.models import Conversation, Message, Lead, EventLog
from app.schemas.lead import LeadData, LeadUpdate
from app.schemas.conversation import MessageRecord
from datetime import datetime
from typing import List, Optional


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_conversation(self, user_id: str, channel: str) -> Conversation:
        conv = self.db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.channel == channel
        ).first()
        if not conv:
            conv = Conversation(user_id=user_id, channel=channel)
            self.db.add(conv)
            self.db.commit()
            self.db.refresh(conv)
        else:
            conv.last_activity = datetime.utcnow()
            self.db.commit()
        return conv

    def get_recent_messages(self, user_id: str, channel: str, limit: int = 10) -> List[Message]:
        return self.db.query(Message).filter(
            Message.user_id == user_id,
            Message.channel == channel
        ).order_by(desc(Message.timestamp)).limit(limit).all()

    def save_message(self, record: MessageRecord) -> Message:
        msg = Message(
            user_id=record.user_id,
            channel=record.channel,
            message_in=record.message_in,
            message_out=record.message_out,
            intent=record.intent,
            confidence=record.confidence,
            escalated=record.escalated,
            metadata_=record.metadata,
        )
        self.db.add(msg)
        # Update conversation counter
        conv = self.get_or_create_conversation(record.user_id, record.channel)
        conv.message_count = (conv.message_count or 0) + 1
        conv.last_activity = datetime.utcnow()
        self.db.commit()
        self.db.refresh(msg)
        return msg


class LeadRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_lead(self, user_id: str, channel: str) -> Optional[Lead]:
        return self.db.query(Lead).filter(
            Lead.user_id == user_id,
            Lead.channel == channel
        ).first()

    def create_or_update_lead(self, data: LeadData) -> Lead:
        lead = self.get_lead(data.user_id, data.channel)
        if not lead:
            lead = Lead(
                user_id=data.user_id,
                channel=data.channel,
                fecha_creacion=datetime.utcnow(),
            )
            self.db.add(lead)

        # Update only non-None fields
        for field in ["nombre", "empresa", "rubro", "cargo", "email", "telefono",
                      "canal_preferido", "problema_principal", "servicio_interesado",
                      "presupuesto_estimado", "urgencia", "mensaje_original", "estado"]:
            val = getattr(data, field, None)
            if val is not None:
                setattr(lead, field, val)

        lead.fecha_actualizacion = datetime.utcnow()
        self.db.commit()
        self.db.refresh(lead)
        return lead

    def list_leads(self, limit: int = 100) -> List[Lead]:
        return self.db.query(Lead).order_by(desc(Lead.fecha_creacion)).limit(limit).all()

    def update_lead_status(self, user_id: str, channel: str, estado: str) -> Optional[Lead]:
        lead = self.get_lead(user_id, channel)
        if lead:
            lead.estado = estado
            lead.fecha_actualizacion = datetime.utcnow()
            self.db.commit()
            self.db.refresh(lead)
        return lead


class EventLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def log(self, event_type: str, user_id: str = None, channel: str = None,
            description: str = None, payload: dict = None):
        event = EventLog(
            event_type=event_type,
            user_id=user_id,
            channel=channel,
            description=description,
            payload=payload,
        )
        self.db.add(event)
        self.db.commit()
