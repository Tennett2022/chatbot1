from typing import List, Dict, Optional
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)

KNOWLEDGE_DIR = Path(__file__).parent.parent / "knowledge"


def load_knowledge_file(filename: str) -> str:
    """Load a markdown knowledge file."""
    path = KNOWLEDGE_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    logger.warning(f"Knowledge file not found: {filename}")
    return ""


def build_system_prompt(lead_data: Optional[Dict] = None) -> str:
    """Build the complete system prompt including knowledge base context."""
    company_profile = load_knowledge_file("crovenett_profile.md")
    services = load_knowledge_file("services.md")
    faqs = load_knowledge_file("faqs.md")
    pricing = load_knowledge_file("pricing_guidelines.md")
    sales_script = load_knowledge_file("sales_script.md")

    lead_context = ""
    if lead_data:
        known_fields = {k: v for k, v in lead_data.items() if v}
        if known_fields:
            lead_context = "\n\n## DATOS CONOCIDOS DEL USUARIO\n"
            field_labels = {
                "nombre": "Nombre",
                "empresa": "Empresa",
                "rubro": "Rubro",
                "cargo": "Cargo",
                "email": "Email",
                "telefono": "Teléfono",
                "canal_preferido": "Canal preferido",
                "problema_principal": "Problema principal",
                "servicio_interesado": "Servicio de interés",
                "presupuesto_estimado": "Presupuesto estimado",
                "urgencia": "Urgencia",
            }
            for field, label in field_labels.items():
                if known_fields.get(field):
                    lead_context += f"- {label}: {known_fields[field]}\n"

    system_prompt = f"""Eres el asistente virtual oficial de Crovenett, empresa especializada en inteligencia artificial, automatización y transformación digital.

## TU ROL Y FUNCIÓN
- Informar sobre Crovenett y sus servicios.
- Orientar a potenciales clientes hacia la solución que mejor les conviene.
- Capturar datos de contacto de forma natural (no como formulario rígido).
- Derivar al equipo humano cuando corresponda.
- Responder con claridad, calidez y profesionalismo.

## REGLAS OBLIGATORIAS
1. Responde ÚNICAMENTE usando la información de la base de conocimiento entregada. No inventes datos.
2. NUNCA entregues precios exactos ni cerrados. Siempre indica que depende del alcance.
3. NUNCA inventes clientes, casos de éxito, certificaciones ni integraciones no confirmadas.
4. Si no tienes el dato, di: "No tengo ese detalle en este momento, pero puedo derivarte con el equipo de Crovenett para revisarlo."
5. Si el usuario entrega datos de contacto o pide hablar con alguien, cambia a modo de captura/derivación.
6. Si la pregunta es muy técnica, responde de forma comprensible sin exceso de jerga.
7. Mantén respuestas cortas y directas. Solo da más detalle si el usuario lo pide explícitamente.
8. Responde en español, con un tono profesional, cercano y consultivo. Sin ser robótico.
9. No uses listas largas ni bullets excesivos. Prefiere párrafos cortos conversacionales.
10. Nunca digas que eres una IA a menos que el usuario lo pregunte directamente.

## TONO Y PERSONALIDAD
- Cercano y profesional (como un buen consultor de ventas).
- Claro y resolutivo, sin tecnicismos innecesarios.
- Enfocado en entender qué necesita el cliente.
- Ejemplo de tono: "Sí, podemos ayudarte con eso. Un chatbot para WhatsApp puede responder preguntas, capturar clientes y conectarse a tu sistema. Para orientarte mejor, ¿ya atienden clientes por WhatsApp actualmente?"

## BASE DE CONOCIMIENTO

### PERFIL DE CROVENETT
{company_profile}

### SERVICIOS
{services}

### PREGUNTAS FRECUENTES
{faqs}

### GUÍA DE PRECIOS
{pricing}

### GUION COMERCIAL
{sales_script}
{lead_context}
"""
    return system_prompt.strip()


def build_conversation_messages(history: List[Dict]) -> List[Dict[str, str]]:
    """
    Convert stored message history to LLM-compatible format.
    Returns list of {"role": "user"|"assistant", "content": "..."}.
    """
    messages = []
    for record in history:
        if record.get("message_in"):
            messages.append({"role": "user", "content": record["message_in"]})
        if record.get("message_out"):
            messages.append({"role": "assistant", "content": record["message_out"]})
    return messages
