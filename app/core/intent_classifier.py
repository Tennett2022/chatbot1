import re
from typing import Tuple

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Intents ordered by evaluation priority (more specific first)
# First match wins, so put narrow patterns before broad ones.
INTENTS: dict[str, list[str]] = {
    # ── Channel-specific chatbot requests (most specific — check before generic "servicios") ──
    "chatbot_whatsapp": [
        r"\b(chatbot|bot)\s*(para|de|en)?\s*whatsapp\b",
        r"\bwhatsapp\s*(chatbot|bot|automatiz)\b",
        r"\bautomat\w+\s*(el\s*)?whatsapp\b",
    ],
    "chatbot_telegram": [
        r"\b(chatbot|bot)\s*(para|de|en)?\s*telegram\b",
        r"\btelegram\s*(chatbot|bot)\b",
    ],
    "chatbot_web": [
        r"\b(chatbot|bot|chat)\s*(para|de|en)?\s*(mi\s*)?(p[aá]gina|web|sitio|website)\b",
        r"\bwidget\s*de\s*chat\b",
        r"\bchat\s*embebido\b",
    ],
    "voicebot": [
        r"\bvoicebot\b",
        r"\bbot\s*de\s*voz\b",
        r"\basistente\s*de\s*voz\b",
        r"\bresponder?\s*(llamadas?|tel[eé]fono)\s*autom[aá]tic\b",
        r"\bivr\b",
    ],

    # ── Commercial actions ────────────────────────────────────────────────────
    "agendar_reunion": [
        r"\b(agendar?|programar?|coordinar?)\s*(una\s*)?(reuni[oó]n|llamada|videollamada|demo|visita)\b",
        r"\b(quiero|quisiera|me\s*gustar[ií]a)\s*(una\s*)?(demo|reuni[oó]n|llamada)\b",
        r"\b(zoom|meet|teams)\s*(para\s*(ver|revisar|conocer))?\b",
        r"\bhablar\s*por\s*tel[eé]fono\b",
    ],
    "soporte_humano": [
        r"\b(hablar|contactar|comunicarme)\s*(con\s*)?(alguien|una\s*persona|un\s*humano|un\s*ejecutivo|el\s*equipo|un\s*asesor|un\s*representante)\b",
        r"\b(quiero|necesito)\s*que\s*(me\s*)?(llamen|contacten|escriban)\b",
        r"\batenci[oó]n\s*(humana|personal)\b",
        r"\bderivame\b",
    ],
    "cliente_interesado": [
        r"\b(me\s*interesa|estoy\s*interesado|quiero\s*contratar|quisiera\s*contratar)\b",
        r"\bc[oó]mo\s*(contrato|empiezo|arrancamos|parti\w+)\b",
        r"\bcuando\s*podemos\s*empezar\b",
        r"\bquiero\s*implementar\b",
    ],
    "precios": [
        r"\b(precio|costo|cu[aá]nto\s*(cuesta|vale|cobran?|sale)|tarifa|valor)\b",
        r"\bpresupuesto\b",
        r"\bcotiz(ar|aci[oó]n)\b",
        r"\bcu[aá]nto\s*me\s*sale\b",
    ],

    # ── Information requests ──────────────────────────────────────────────────
    "informacion_empresa": [
        r"\bqu[eé]\s*(hace[ns]?|es|son)\s*(crovenett|la\s*empresa|ustedes)\b",
        r"\b(cu[eé]ntame|inf[oó]rmame|d[ií]game)\s*(sobre\s*)?(ustedes|la\s*empresa|crovenett)\b",
        r"\ba\s*qu[eé]\s*se\s*dedica[ns]?\b",
        r"\bqui[eé]nes\s*(son|somos)\b",
        r"\bsobre\s*ustedes\b",
    ],
    "servicios": [
        r"\bqu[eé]\s*(servicios?|soluciones?|productos?)\s*(ofrecen?|tienen?|hay)\b",
        r"\bcu[aá]les\s*son\s*(sus\s*)?(servicios?|soluciones?)\b",
        r"\bqu[eé]\s*hacen\b",
        r"\bqu[eé]\s*ofrecen\b",
    ],
    "automatizacion": [
        r"\bautomatiz\w+\b",
        r"\bflujo\s*autom[aá]tic\b",
        r"\bn8n\b",
        r"\b(make|zapier|integromat)\b",
        r"\bproceso\s*autom[aá]tic\b",
    ],
    "generacion_leads": [
        r"\b(generar?|captaci[oó]n\s*de|conseguir|obtener)\s*leads?\b",
        r"\bleads?\b",
        r"\bcaptar\s*clientes?\b",
        r"\bprospectos?\b",
        r"\bbase\s*de\s*datos?\s*de\s*clientes?\b",
    ],
    "integraciones": [
        r"\bintegra\w+\b",
        r"\bconectar\s*(con|a)\b",
        r"\b(crm|hubspot|salesforce|pipedrive)\b",
        r"\b(gmail|google\s*calendar|google\s*sheets?)\b",
        r"\bbase\s*de\s*datos\b",
        r"\bapi\b",
    ],
    "pregunta_tecnica": [
        r"\b(webhook|arquitectura|llm|embedding|rag|vector|docker)\b",
        r"\b(gpt|claude|gemini)\s*(modelo|api|integraci[oó]n)\b",
        r"\bcomo\s*(funciona|implementa)\s*(la\s*ia|el\s*bot)\b",
    ],

    # ── Conversation framing ──────────────────────────────────────────────────
    "saludo": [
        r"\b(hola|buenas|buen\s*d[ií]a|buenos?\s*d[ií]as|buen[ao]s?\s*tard[ae]s|buen[ao]s?\s*noch[ae]s)\b",
        r"\bhey\b",
        r"\bqu[eé]\s*tal\b",
        r"\bc[oó]mo\s*est[aá]s?\b",
        r"\bsaludos\b",
    ],
    "despedida": [
        r"\b(adi[oó]s|hasta\s*luego|hasta\s*pronto|nos\s*vemos|chao|ciao|bye)\b",
        r"\bgracias\s*(y\s*adi[oó]s|por\s*todo|fue\s*todo)\b",
        r"\beso\s*es\s*todo\b",
    ],
}


def classify_intent(text: str) -> Tuple[str, float]:
    """
    Classify the intent of a user message using ordered regex rules.
    More specific intents are checked before generic ones.

    Returns:
        (intent_name, confidence)
        confidence = 0.9 for a pattern match, 0.3 for fallback.
    """
    if not text or not text.strip():
        return "fuera_de_alcance", 0.3

    normalized = text.lower().strip()

    for intent, patterns in INTENTS.items():
        for pattern in patterns:
            try:
                if re.search(pattern, normalized, re.IGNORECASE):
                    logger.debug(f"Intent='{intent}' matched pattern for: '{text[:60]}'")
                    return intent, 0.9
            except re.error as exc:
                logger.warning(f"Regex error in intent '{intent}': {exc}")

    logger.debug(f"No intent matched for: '{text[:60]}'")
    return "fuera_de_alcance", 0.3
