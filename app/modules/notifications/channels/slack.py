# Canal de notificaciones via Slack webhook
import httpx
import logging
from app.core.config import config

logger = logging.getLogger(__name__)


async def enviar_slack(mensaje: str) -> bool:
    """
    Envia un mensaje a Slack.
    Si el webhook es placeholder o vacio, solo loguea el mensaje.
    Nunca lanza excepcion.
    """
    url = getattr(config, "SLACK_WEBHOOK_URL", None)
    if not url or url == "placeholder":
        logger.info(f"[SLACK-SIMULADO] {mensaje}")
        return True
    try:
        async with httpx.AsyncClient(timeout=10.0) as cliente:
            respuesta = await cliente.post(url, json={"text": mensaje})
            return respuesta.status_code == 200
    except Exception as e:
        logger.warning(f"Error al enviar notificacion Slack: {e}")
        return False
