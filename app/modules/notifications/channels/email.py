# Canal de notificaciones via email con Resend
import logging
from app.core.config import config

logger = logging.getLogger(__name__)


async def enviar_email(destinatario: str, asunto: str, cuerpo_html: str) -> bool:
    """
    Envia un email via Resend API.
    Si la API key es placeholder o vacia, solo loguea el mensaje.
    Nunca lanza excepcion.
    """
    api_key = getattr(config, "RESEND_API_KEY", None)
    if not api_key or api_key == "placeholder":
        logger.info(f"[EMAIL-SIMULADO] Para: {destinatario} | Asunto: {asunto}")
        return True
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            respuesta = await cliente.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "from": "noreply@automatizacion-dolibarr.com",
                    "to": [destinatario],
                    "subject": asunto,
                    "html": cuerpo_html,
                },
            )
            return respuesta.status_code in (200, 201)
    except Exception as e:
        logger.warning(f"Error al enviar email a {destinatario}: {e}")
        return False
