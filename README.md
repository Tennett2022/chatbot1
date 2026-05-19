# Crovenett Chatbot

Chatbot empresarial multicanal con inteligencia artificial para **Crovenett**.

Actúa como el cerebro comercial y operativo de Crovenett: responde preguntas sobre la empresa, explica servicios, orienta a clientes potenciales, captura leads y deriva solicitudes al equipo humano cuando corresponde.

## Características principales

- **Integración con Telegram** — webhook listo para producción
- **Arquitectura preparada para WhatsApp** — soporte para Meta, Twilio, Evolution API, WATI, Z-API
- **Motor de IA configurable** — compatible con OpenAI, Anthropic (Claude) y Google Gemini
- **Base de conocimiento editable** — archivos Markdown que el bot usa como contexto
- **Captura de leads automática** — extrae nombre, empresa, email, teléfono y más de la conversación
- **Escalamiento inteligente** — deriva a humano cuando detecta intención comercial alta
- **Guardrails de seguridad** — evita inventar precios, clientes o certificaciones
- **Memoria conversacional** — mantiene historial de mensajes por usuario
- **SQLite por defecto**, con abstracción para migrar a PostgreSQL
- **Docker y docker-compose** incluidos

---

## Estructura del proyecto

```
crovenett-chatbot/
├── app/
│   ├── main.py                    # Punto de entrada FastAPI
│   ├── config.py                  # Configuración desde .env
│   ├── routes/
│   │   ├── health.py              # GET /health
│   │   ├── telegram_webhook.py    # POST /webhook/telegram
│   │   └── whatsapp_webhook.py    # POST /webhook/whatsapp
│   ├── channels/
│   │   ├── base_channel.py        # Interfaz abstracta de canal
│   │   ├── telegram_channel.py    # Implementación Telegram
│   │   └── whatsapp_channel.py    # Stub multi-proveedor WhatsApp
│   ├── core/
│   │   ├── chatbot_engine.py      # Motor principal del chatbot
│   │   ├── prompt_builder.py      # Construcción del prompt del LLM
│   │   ├── intent_classifier.py   # Clasificación de intención del usuario
│   │   ├── lead_extractor.py      # Extracción de datos del lead
│   │   ├── escalation.py          # Lógica de escalamiento a humano
│   │   └── response_guardrails.py # Filtros de seguridad de respuestas
│   ├── llm/
│   │   ├── base_llm.py            # Interfaz abstracta LLM
│   │   ├── openai_provider.py     # Proveedor OpenAI
│   │   ├── anthropic_provider.py  # Proveedor Anthropic (Claude)
│   │   └── gemini_provider.py     # Proveedor Google Gemini
│   ├── knowledge/
│   │   ├── crovenett_profile.md   # Perfil de la empresa
│   │   ├── services.md            # Descripción de servicios
│   │   ├── faqs.md                # Preguntas frecuentes
│   │   ├── pricing_guidelines.md  # Guía de precios (sin valores exactos)
│   │   └── sales_script.md        # Guion comercial del bot
│   ├── storage/
│   │   ├── database.py            # Configuración SQLAlchemy
│   │   ├── models.py              # Modelos de base de datos
│   │   └── repositories.py        # Capa de acceso a datos
│   ├── schemas/
│   │   ├── message.py             # Esquemas de mensaje entrante/saliente
│   │   ├── lead.py                # Esquema de lead
│   │   └── conversation.py        # Esquema de conversación
│   └── utils/
│       ├── logger.py              # Logger estructurado
│       └── text.py                # Utilidades de texto
├── tests/
│   ├── test_intent_classifier.py
│   ├── test_lead_extractor.py
│   └── test_prompt_builder.py
├── .env.example
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Instalación local

### Requisitos previos
- Python 3.11 o superior

### 1. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores reales. Mínimo necesario:

```env
TELEGRAM_BOT_TOKEN=tu_token_de_telegram
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

### 3. Levantar el servidor

```bash
uvicorn app.main:app --reload --port 8000
```

Verifica:
```bash
curl http://localhost:8000/health
```

---

## Crear un bot en Telegram

1. Abre Telegram y busca **@BotFather**
2. Envía `/newbot`
3. Elige nombre y username (debe terminar en `bot`)
4. Copia el token en `.env` como `TELEGRAM_BOT_TOKEN`

---

## Configurar webhook con ngrok

```bash
# Instalar ngrok: https://ngrok.com/download
ngrok http 8000
```

Registrar el webhook (reemplaza `abc123` con tu URL de ngrok):

```bash
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://abc123.ngrok.io/webhook/telegram"}'
```

O usa el endpoint de desarrollo:

```bash
curl -X POST "http://localhost:8000/webhook/telegram/set?webhook_url=https://abc123.ngrok.io/webhook/telegram"
```

Verificar webhook activo:

```bash
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

---

## Probar el bot en Telegram

1. Busca tu bot en Telegram
2. Envía `/start` o `Hola`
3. Prueba con preguntas:
   - "¿Qué servicios ofrecen?"
   - "Necesito un chatbot para WhatsApp"
   - "¿Cuánto cuesta?"
   - "Quiero hablar con alguien"

---

## Editar la base de conocimiento

Los archivos en `app/knowledge/` son Markdown editables. Los cambios se reflejan en tiempo real.

| Archivo | Contenido |
|---|---|
| `crovenett_profile.md` | Descripción, misión, valores de la empresa |
| `services.md` | Lista detallada de servicios |
| `faqs.md` | Preguntas frecuentes y respuestas |
| `pricing_guidelines.md` | Política de precios (sin valores exactos) |
| `sales_script.md` | Guion comercial y frases recomendadas |

---

## Cambiar proveedor de LLM

En `.env`:

```env
# OpenAI
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini

# Anthropic (Claude)
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-haiku-20241022

# Google Gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=AI...
GEMINI_MODEL=gemini-1.5-flash
```

Para agregar un nuevo proveedor: crea un archivo en `app/llm/` que extienda `BaseLLM` y regístralo en `app/llm/__init__.py`.

---

## Activar WhatsApp — Guía por proveedor

El sistema soporta 4 proveedores. Elige uno y sigue los pasos.

### Opción A: Meta WhatsApp Cloud API (oficial, recomendado)

**Requisitos**: cuenta de Meta for Developers, número verificado.

```bash
# 1. Configura las variables
WHATSAPP_PROVIDER=meta
WHATSAPP_TOKEN=EAABs...        # Access Token de tu app
WHATSAPP_PHONE_NUMBER_ID=123456789
WHATSAPP_VERIFY_TOKEN=mi_token_secreto   # lo inventas tú
```

**Configurar el webhook en Meta:**
1. Ve a [developers.facebook.com](https://developers.facebook.com) → tu app → WhatsApp → Configuración
2. Webhook URL: `https://tu-dominio.com/webhook/whatsapp`
3. Verify Token: el mismo valor que pusiste en `WHATSAPP_VERIFY_TOKEN`
4. Suscríbete al evento: `messages`

**El código ya está listo** — `_parse_meta()` y `_send_meta()` en `whatsapp_channel.py` están implementados.

---

### Opción B: Evolution API (self-hosted, open source)

**Requisitos**: servidor con Evolution API instalada.

```bash
WHATSAPP_PROVIDER=evolution
WHATSAPP_TOKEN=http://tu-servidor:8080  # URL base de Evolution API
WHATSAPP_PHONE_NUMBER_ID=nombre_instancia
```

**Pasos:**
1. Instala Evolution API: `docker run -p 8080:8080 atendai/evolution-api`
2. Crea una instancia y escanea el QR de WhatsApp
3. Configura el webhook de Evolution apuntando a: `https://tu-dominio.com/webhook/whatsapp`
4. En `app/channels/whatsapp_channel.py`, el método `_parse_evolution()` ya tiene el parser — revisa el formato exacto de tu versión de Evolution API y ajusta si es necesario.

---

### Opción C: WATI

```bash
WHATSAPP_PROVIDER=wati
WHATSAPP_TOKEN=tu_api_key_de_wati
WHATSAPP_PHONE_NUMBER_ID=tu_numero_wati
```

En `app/channels/whatsapp_channel.py`, implementa `_send_wati()`:
```python
async def _send_wati(self, message: OutgoingMessage) -> bool:
    url = f"https://live-server.wati.io/api/v1/sendSessionMessage/{message.user_id}"
    headers = {"Authorization": f"Bearer {settings.WHATSAPP_TOKEN}"}
    payload = {"messageText": message.text}
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        return resp.status_code == 200
```

---

### Opción D: Twilio

```bash
WHATSAPP_PROVIDER=twilio
WHATSAPP_TOKEN=tu_auth_token
WHATSAPP_PHONE_NUMBER_ID=whatsapp:+14155238886   # número Twilio sandbox
```

Twilio envía datos `form-encoded`. El webhook de FastAPI debe recibir `Form()` en vez de JSON para este caso. Ver nota en `whatsapp_webhook.py`.

---

### Verificar que WhatsApp funciona

```bash
# Envía un mensaje desde tu celular al número configurado
# Revisa los logs del servidor
docker-compose logs -f chatbot | grep whatsapp
```

---

## Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/health` | Estado del servicio |
| `POST` | `/webhook/telegram` | Recibir mensajes de Telegram |
| `GET` | `/webhook/whatsapp` | Verificación webhook Meta |
| `POST` | `/webhook/whatsapp` | Recibir mensajes de WhatsApp |
| `GET` | `/leads` | Listar leads capturados |
| `GET` | `/conversations/{user_id}` | Historial de conversación |
| `GET` | `/docs` | Documentación Swagger UI |

---

## Ejecutar tests

```bash
# Todos los tests
pytest tests/ -v

# Módulo específico
pytest tests/test_intent_classifier.py -v

# Con cobertura
pytest tests/ --cov=app --cov-report=term-missing
```

---

## Despliegue con Docker

```bash
cp .env.example .env
# Editar .env con valores reales

docker-compose up --build -d
docker-compose logs -f chatbot
```

---

## Migración a PostgreSQL

1. Instala el driver: `pip install psycopg2-binary`
2. Cambia en `.env`:
   ```env
   DATABASE_URL=postgresql://usuario:password@host:5432/crovenett_chatbot
   ```
3. El resto del código no cambia.

---

## Variables de entorno — referencia

| Variable | Descripción | Ejemplo |
|---|---|---|
| `APP_ENV` | Entorno | `development` |
| `LOG_LEVEL` | Nivel de logging | `INFO` |
| `TELEGRAM_BOT_TOKEN` | Token del bot Telegram | `123456:ABC...` |
| `TELEGRAM_WEBHOOK_SECRET` | Secreto webhook | `mi_secreto` |
| `WHATSAPP_PROVIDER` | Proveedor WhatsApp | `meta` |
| `WHATSAPP_TOKEN` | Token WhatsApp | `EAABs...` |
| `WHATSAPP_PHONE_NUMBER_ID` | ID número Meta | `123456789` |
| `WHATSAPP_VERIFY_TOKEN` | Token verificación webhook | `mi_verify` |
| `LLM_PROVIDER` | Proveedor IA | `openai` |
| `OPENAI_API_KEY` | API key OpenAI | `sk-...` |
| `OPENAI_MODEL` | Modelo OpenAI | `gpt-4o-mini` |
| `ANTHROPIC_API_KEY` | API key Anthropic | `sk-ant-...` |
| `ANTHROPIC_MODEL` | Modelo Claude | `claude-3-5-haiku-20241022` |
| `GEMINI_API_KEY` | API key Gemini | `AI...` |
| `DATABASE_URL` | URL base de datos | `sqlite:///./chat.db` |
| `MAX_HISTORY_MESSAGES` | Mensajes de historial | `10` |

---

## Soporte

Proyecto desarrollado para **Crovenett**. Contacto: contacto@crovenett.cl
