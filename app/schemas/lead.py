from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LeadData(BaseModel):
    user_id: str
    channel: str
    nombre: Optional[str] = None
    empresa: Optional[str] = None
    rubro: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    canal_preferido: Optional[str] = None
    problema_principal: Optional[str] = None
    servicio_interesado: Optional[str] = None
    presupuesto_estimado: Optional[str] = None
    urgencia: Optional[str] = None
    mensaje_original: Optional[str] = None
    estado: str = "nuevo"  # nuevo | pendiente_contacto | contactado | cerrado
    fecha_creacion: Optional[datetime] = None


class LeadUpdate(BaseModel):
    nombre: Optional[str] = None
    empresa: Optional[str] = None
    rubro: Optional[str] = None
    cargo: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    canal_preferido: Optional[str] = None
    problema_principal: Optional[str] = None
    servicio_interesado: Optional[str] = None
    presupuesto_estimado: Optional[str] = None
    urgencia: Optional[str] = None
    estado: Optional[str] = None
