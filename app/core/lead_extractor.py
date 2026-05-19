import re
from typing import Dict, Optional
from app.utils.text import extract_email, extract_phone
from app.utils.logger import get_logger

logger = get_logger(__name__)


def extract_lead_data(text: str, existing: Optional[Dict] = None) -> Dict:
    """
    Extract lead fields from a user message.
    Returns a dict of detected fields (only non-None values).
    """
    extracted = {}
    normalized = text.lower().strip()

    # Email
    email = extract_email(text)
    if email:
        extracted["email"] = email

    # Phone
    phone = extract_phone(text)
    if phone:
        extracted["telefono"] = phone

    # Name patterns: "me llamo X", "soy X", "mi nombre es X"
    name_match = re.search(
        r'\b(?:me\s+llamo|soy|mi\s+nombre\s+es)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',
        text, re.IGNORECASE
    )
    if name_match:
        extracted["nombre"] = name_match.group(1).strip()

    # Company patterns
    company_match = re.search(
        r'\b(?:de\s+la\s+empresa|trabajo\s+en|mi\s+empresa\s+(?:es|se\s+llama)|empresa)\s+'
        r'([A-Za-záéíóúñÁÉÍÓÚÑ0-9\s&.,\-]+?)(?:\s*[,\.;]|$)',
        text, re.IGNORECASE
    )
    if company_match:
        extracted["empresa"] = company_match.group(1).strip()

    # Sector/rubro
    rubro_keywords = {
        "restaurante": ["restaurante", "comida", "gastronomía", "delivery", "food"],
        "clínica": ["clínica", "médico", "salud", "dental", "hospital"],
        "inmobiliaria": ["inmobiliaria", "arriendos", "bienes raíces", "propiedades"],
        "comercio": ["comercio", "tienda", "retail", "venta"],
        "educación": ["educación", "colegio", "universidad", "instituto", "academia"],
        "servicios profesionales": ["abogado", "contador", "consultoría", "asesoría"],
        "pyme": ["pyme", "pequeña empresa", "microempresa"],
        "tecnología": ["tecnología", "startup", "software", "tech"],
    }
    for rubro, keywords in rubro_keywords.items():
        if any(kw in normalized for kw in keywords):
            extracted["rubro"] = rubro
            break

    # Urgency signals
    if any(w in normalized for w in ["urgente", "urgency", "rápido", "cuanto antes", "pronto", "inmediato"]):
        extracted["urgencia"] = "alta"
    elif any(w in normalized for w in ["no hay prisa", "cuando puedan", "sin apuro"]):
        extracted["urgencia"] = "baja"

    # Service interest from intent signals
    service_patterns = {
        "chatbot_whatsapp": ["whatsapp", "chat para whatsapp"],
        "chatbot_web": ["chatbot web", "widget", "chat en mi página"],
        "chatbot_telegram": ["telegram", "bot de telegram"],
        "voicebot": ["voicebot", "voz", "llamadas"],
        "automatizacion": ["automatización", "flujo automático", "n8n", "make", "zapier"],
        "integraciones": ["integración", "conectar", "crm", "gmail"],
        "generacion_leads": ["leads", "captar clientes", "prospectos"],
    }
    for service, keywords in service_patterns.items():
        if any(kw in normalized for kw in keywords):
            extracted["servicio_interesado"] = service
            break

    # Budget signals
    budget_patterns = [
        (r'\$\s*(\d[\d.,]*)', lambda m: f"${m.group(1)}"),
        (r'(\d[\d.,]*)\s*(usd|eur|clp|pesos?|d[oó]lares?)', lambda m: f"{m.group(1)} {m.group(2)}"),
        (r'presupuesto\s+(?:de\s+)?(\d[\d.,]*)', lambda m: f"${m.group(1)}"),
    ]
    for pattern, formatter in budget_patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            extracted["presupuesto_estimado"] = formatter(m)
            break

    if extracted:
        logger.info(f"Lead data extracted: {list(extracted.keys())}")

    return extracted


def get_missing_lead_fields(lead_data: Dict) -> list:
    """Return list of important lead fields that are still missing."""
    priority_fields = ["nombre", "empresa", "email", "telefono"]
    return [f for f in priority_fields if not lead_data.get(f)]
