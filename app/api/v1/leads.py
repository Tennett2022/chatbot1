from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.permissions import get_current_user
from app.schemas.lead import LeadData
from app.storage.database import get_db
from app.storage.models import Lead
from app.storage.repositories import LeadRepository

router = APIRouter()


def _serialize(lead: Lead) -> dict:
    return {
        "id": lead.id,
        "user_id": lead.user_id,
        "channel": lead.channel,
        "nombre": lead.nombre,
        "empresa": lead.empresa,
        "rubro": lead.rubro,
        "cargo": lead.cargo,
        "email": lead.email,
        "telefono": lead.telefono,
        "canal_preferido": lead.canal_preferido,
        "problema_principal": lead.problema_principal,
        "servicio_interesado": lead.servicio_interesado,
        "presupuesto_estimado": lead.presupuesto_estimado,
        "urgencia": lead.urgencia,
        "estado": lead.estado,
        "fecha_creacion": lead.fecha_creacion,
        "fecha_actualizacion": lead.fecha_actualizacion,
    }


@router.get("/leads", tags=["Leads"], summary="List all leads")
async def list_leads(
    limit: int = 100,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return the most recent leads. Requires authentication."""
    repo = LeadRepository(db)
    return [_serialize(l) for l in repo.list_leads(limit=limit)]


@router.get("/leads/{lead_id}", tags=["Leads"], summary="Get a lead by ID")
async def get_lead(
    lead_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """Return a specific lead by its database ID. Requires authentication."""
    lead = db.query(Lead).filter(Lead.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead no encontrado.")
    return _serialize(lead)


@router.post("/leads", tags=["Leads"], status_code=201, summary="Create or update a lead")
async def create_lead(
    data: LeadData,
    db: Session = Depends(get_db),
    _: dict = Depends(get_current_user),
):
    """
    Manually create or update a lead from an external system.
    Requires authentication.
    """
    repo = LeadRepository(db)
    lead = repo.create_or_update_lead(data)
    return _serialize(lead)
