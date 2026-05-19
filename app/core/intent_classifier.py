import re
from typing import Tuple
from app.utils.logger import get_logger

logger = get_logger(__name__)

INTENTS = {
    "saludo": [
        r"\b(hola|buenas|buen\s*d[ií]a|buen\s*tarde|buen\s*noche|hey|saludos|qu[eé]\s*tal|c[oó]mo\s*est[aá]s)\b"
    ],
    "informacion_empresa": [
        r"\b(qu[eé]\s*(hace[ns]?|son|es crovenett|ofrece[ns]?)|cu[eé]ntame|sobre\s+ustedes|a\s+qu[eé]\s+se\s+dedica|qui[eé]nes\s+son)\b"
    ],
    "servicios": [
        r"\b(servicios?|soluciones?|productos?|qu[eé]\s+ofrecen|cu[aá]les\s+son)\b"
    ],
    "chatbot_whatsapp": [
        r"\b(chatbot.*whatsapp|whatsapp.*chatbot|bot.*whatsapp|whatsapp.*bot|chatbot\s+para\s+whatsapp)\b"
    ],
    "chatbot_telegram": [
        r"\b(chatbot.*telegram|telegram.*chatbot|bot.*telegram|telegram.*bot)\b"
    ],
    "chatbot_web": [
        r"\b(chatbot.*web|web.*chatbot|bot.*p[aá]gina|chat.*p[aá]gina|widget)\b"
    ],
    "voicebot": [
        r"\b(voicebot|voice\s*bot|bot\s*de\s*voz|asistente\s*de\s*voz|respuesta\s*de\s*voz|ivr)\b"
    ],
    "automatizacion": [
        r"\b(automatiz|flujo\s*autom|proceso\s*autom|n8n|make|zapier|integromat)\b"
    ],
    "generacion_leads": [
        r"\b(leads?|captar\s*clientes?|conseguir\s*clientes?|prospectos?|generaci[oó]n\s*de\s*contactos?)\b"
    ],
    "integraciones": [
        r"\b(integra|conectar|crm|gmail|calendar|google\s*sheets?|planilla|base\s*de\s*datos|api|hubspot|salesforce)\b"
    ],
    "precios": [
        r"\b(precio|costo|cu[aá]nto\s*(cuesta|vale|cobran?)|tarifa|valor|presupuesto|cotiz)\b"
    ],
    "agendar_reunion": [
        r"\b(agenda|reuni[oó]n|demo|llamada|videollamada|zoom|meet|reun[ií]rse|hablar\s*por\s*tel[eé]fono|coordinar)\b"
    ],
    "soporte_humano": [
        r"\b(hablar\s*con\s*(alguien|una\s*persona|un\s*humano|un\s*ejecutivo|el\s*equipo)|atenci[oó]n\s*humana|quiero\s*que\s*me\s*llamen|contactar|derivar)\b"
    ],
    "cliente_interesado": [
        r"\b(me\s*interesa|estoy\s*interesado|quiero\s*contratar|necesito\s*esto|cuando\s*podemos\s*empezar|c[oó]mo\s*contrato)\b"
    ],
    "pregunta_tecnica": [
        r"\b(api|webhook|arquitectura|tecnolog[ií]a|llm|gpt|claude|gemini|embedding|rag|vector|docker|servidor)\b"
    ],
    "despedida": [
        r"\b(adi[oó]s|hasta\s*luego|chao|hasta\s*pronto|nos\s*vemos|gracias\s*y\s*adi[oó]s|bye)\b"
    ],
}


def classify_intent(text: str) -> Tuple[str, float]:
    """
    Classify the intent of a user message using regex rules.

    Returns:
        Tuple of (intent_name, confidence_score)
        confidence is 0.9 for rule match, 0.3 for fallback.
    """
    normalized = text.lower().strip()

    # Check each intent in priority order
    for intent, patterns in INTENTS.items():
        for pattern in patterns:
            if re.search(pattern, normalized, re.IGNORECASE):
                logger.debug(f"Intent matched: {intent} for text: '{text[:50]}'")
                return intent, 0.9

    logger.debug(f"No intent matched for: '{text[:50]}', defaulting to fuera_de_alcance")
    return "fuera_de_alcance", 0.3
