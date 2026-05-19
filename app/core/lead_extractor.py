import re
from typing import Dict, List, Optional

from app.utils.text import extract_email, extract_phone
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Keywords whose presence invalidates a "soy X" name match
# (professions, roles, adjectives that aren't names)
_NOT_A_NAME = {
    "médico", "doctor", "doctora", "abogado", "abogada", "contador", "contadora",
    "ingeniero", "ingeniera", "gerente", "director", "directora", "dueño", "dueña",
    "empresario", "empresaria", "vendedor", "vendedora", "consultor", "consultora",
    "estudiante", "profesor", "profesora", "enfermero", "enfermera", "cliente",
    "nuevo", "nueva", "interesado", "interesada",
}

RUBRO_KEYWORDS: Dict[str, List[str]] = {
    "restaurante": ["restaurante", "restaurant", "gastronom", "comida", "delivery", "food", "cafetería", "bar"],
    "clínica": ["clínica", "clinica", "médico", "médica", "salud", "dental", "hospital", "psicólogo", "terapeuta"],
    "inmobiliaria": ["inmobiliaria", "arriendos", "bienes raíces", "propiedades", "corredora de propiedades"],
    "comercio": ["comercio", "tienda", "retail", "venta al público", "local comercial", "ferretería", "minimarket"],
    "educación": ["educación", "colegio", "universidad", "instituto", "academia", "capacitación", "cursos"],
    "servicios profesionales": ["abogado", "abogada", "contador", "contadora", "consultoría", "asesoría", "estudio"],
    "pyme": ["pyme", "pequeña empresa", "microempresa", "emprendimiento"],
    "tecnología": ["tecnología", "software", "startup", "tech", "desarrollo web", "aplicación"],
    "agencia": ["agencia", "marketing", "publicidad", "diseño"],
}

SERVICE_KEYWORDS: Dict[str, List[str]] = {
    "chatbot_whatsapp": ["whatsapp", "bot de whatsapp", "chat whatsapp"],
    "chatbot_web": ["chatbot web", "widget", "chat en mi página", "chat en la web", "bot en la web"],
    "chatbot_telegram": ["telegram", "bot de telegram", "chat telegram"],
    "voicebot": ["voicebot", "bot de voz", "voz", "llamadas automáticas", "ivr"],
    "automatizacion": ["automatización", "automatizar", "flujo automático", "n8n", "make", "zapier"],
    "integraciones": ["integración", "conectar con", "crm", "gmail", "google sheets", "planilla"],
    "generacion_leads": ["leads", "captar clientes", "prospectos", "generar contactos"],
    "rag": ["documentos", "rag", "base de conocimiento", "manual", "normativa"],
}


def extract_lead_data(text: str, existing: Optional[Dict] = None) -> Dict:
    """
    Extract structured lead fields from a single user message.

    Only returns fields found in THIS message. Does NOT merge with existing —
    that's the engine's responsibility. Does NOT overwrite existing non-null
    values unless a new value is explicitly found.

    Args:
        text:     The raw user message.
        existing: Already-known lead fields (used to skip re-extraction).

    Returns:
        Dict of newly extracted fields (may be empty).
    """
    existing = existing or {}
    extracted: Dict = {}
    normalized = text.lower().strip()

    # ── Email ─────────────────────────────────────────────────────────────────
    if not existing.get("email"):
        email = extract_email(text)
        if email:
            extracted["email"] = email

    # ── Phone ─────────────────────────────────────────────────────────────────
    if not existing.get("telefono"):
        phone = extract_phone(text)
        if phone:
            extracted["telefono"] = phone

    # ── Name ──────────────────────────────────────────────────────────────────
    if not existing.get("nombre"):
        nombre = _extract_name(text)
        if nombre:
            extracted["nombre"] = nombre

    # ── Company ───────────────────────────────────────────────────────────────
    if not existing.get("empresa"):
        empresa = _extract_company(text)
        if empresa:
            extracted["empresa"] = empresa

    # ── Rubro / Sector ────────────────────────────────────────────────────────
    if not existing.get("rubro"):
        for rubro, keywords in RUBRO_KEYWORDS.items():
            if any(kw in normalized for kw in keywords):
                extracted["rubro"] = rubro
                break

    # ── Service Interest ──────────────────────────────────────────────────────
    if not existing.get("servicio_interesado"):
        for service, keywords in SERVICE_KEYWORDS.items():
            if any(kw in normalized for kw in keywords):
                extracted["servicio_interesado"] = service
                break

    # ── Urgency ───────────────────────────────────────────────────────────────
    if not existing.get("urgencia"):
        if any(w in normalized for w in ["urgente", "lo antes posible", "cuanto antes", "inmediato", "urgencia"]):
            extracted["urgencia"] = "alta"
        elif any(w in normalized for w in ["no hay prisa", "cuando puedan", "sin apuro", "con calma"]):
            extracted["urgencia"] = "baja"

    # ── Main Problem ──────────────────────────────────────────────────────────
    # Capture the user's own words about their problem (first 200 chars if long)
    if not existing.get("problema_principal") and len(text) > 40:
        problema = _extract_problem(text, normalized)
        if problema:
            extracted["problema_principal"] = problema[:200]

    # ── Budget ────────────────────────────────────────────────────────────────
    if not existing.get("presupuesto_estimado"):
        budget = _extract_budget(text)
        if budget:
            extracted["presupuesto_estimado"] = budget

    # ── Preferred Channel ─────────────────────────────────────────────────────
    if not existing.get("canal_preferido"):
        canal = _extract_preferred_channel(normalized)
        if canal:
            extracted["canal_preferido"] = canal

    if extracted:
        logger.info(f"Lead fields extracted: {list(extracted.keys())}")

    return extracted


def _extract_name(text: str) -> Optional[str]:
    """
    Extract person name from patterns like:
      "me llamo Carlos Rodríguez"
      "mi nombre es Ana"
      "soy Pedro Soto" (but NOT "soy médico", "soy nuevo")
    """
    # "me llamo X" / "mi nombre es X"
    match = re.search(
        r'\b(?:me\s+llamo|mi\s+nombre\s+es)\s+'
        r'([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{1,20}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{1,20}){0,3})',
        text, re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()

    # "soy X" — only if X looks like a proper name (capitalized, not a profession)
    match = re.search(
        r'\bsoy\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]{1,20}(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]{1,20})?)\b',
        text,
    )
    if match:
        candidate = match.group(1).strip()
        if candidate.lower() not in _NOT_A_NAME:
            return candidate

    return None


def _extract_company(text: str) -> Optional[str]:
    """Extract company name from common patterns."""
    patterns = [
        r'\b(?:trabajo\s+en|de\s+la\s+empresa|mi\s+empresa\s+(?:es|se\s+llama)|represento\s+a)\s+'
        r'([A-Za-záéíóúñÁÉÍÓÚÑ0-9][A-Za-záéíóúñÁÉÍÓÚÑ0-9\s&.,\-]{1,50}?)(?=\s*[,\.;]|\s+y\s|\s+que\b|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).strip().rstrip('.,;')
            if 2 <= len(value) <= 60:
                return value
    return None


def _extract_problem(text: str, normalized: str) -> Optional[str]:
    """Extract the user's stated problem or need."""
    problem_triggers = [
        "necesito", "quiero", "busco", "tenemos", "tengo un problema",
        "necesitamos", "me gustaría", "quisiera",
    ]
    for trigger in problem_triggers:
        if trigger in normalized:
            # Return the portion of the message containing the trigger
            idx = normalized.find(trigger)
            snippet = text[idx:idx + 180].strip()
            if len(snippet) > 20:
                return snippet
    return None


def _extract_budget(text: str) -> Optional[str]:
    """Extract budget mention from the message."""
    patterns = [
        (r'\$\s*([\d.,]+(?:\s*(?:mil|millones?|k|m))?)', lambda m: f"${m.group(1)}"),
        (r'([\d.,]+)\s*(usd|eur|clp|pesos?|d[oó]lares?)', lambda m: f"{m.group(1)} {m.group(2)}"),
        (r'presupuesto\s+(?:de\s+|aproximado\s+de\s+)?([\d.,]+)', lambda m: f"${m.group(1)}"),
    ]
    for pattern, formatter in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return formatter(m)
    return None


def _extract_preferred_channel(normalized: str) -> Optional[str]:
    """Detect which channel the user prefers for communication."""
    if "whatsapp" in normalized:
        return "whatsapp"
    if "telegram" in normalized:
        return "telegram"
    if "correo" in normalized or "email" in normalized or "mail" in normalized:
        return "email"
    if "teléfono" in normalized or "llamada" in normalized or "llamar" in normalized:
        return "telefono"
    return None


def get_missing_lead_fields(lead_data: Dict) -> List[str]:
    """
    Return the list of priority lead fields still missing.
    Phone OR email counts as contact — only flagged missing if both are absent.
    """
    missing = []
    if not lead_data.get("nombre"):
        missing.append("nombre")
    if not lead_data.get("empresa"):
        missing.append("empresa")
    if not lead_data.get("email"):
        missing.append("email")
    if not lead_data.get("telefono"):
        missing.append("telefono")
    return missing
