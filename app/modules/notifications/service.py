# Servicio de notificaciones multi-canal
import logging
from app.modules.notifications.channels.slack import enviar_slack
from app.modules.notifications.channels.email import enviar_email

logger = logging.getLogger(__name__)


def _formatear_monto(monto) -> str:
    """Formatea un monto en formato argentino: $1.234,56"""
    if monto is None:
        return "N/D"
    try:
        valor = float(monto)
    except (TypeError, ValueError):
        return "N/D"
    formato = f"{valor:,.2f}"
    # Cambiar comas por puntos y puntos por comas (formato argentino)
    formato = formato.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"${formato}"


class ServicioNotificaciones:
    """
    Envia notificaciones por distintos canales.
    Si el canal no esta configurado, loguea en lugar de fallar.
    Nunca lanza excepcion - las notificaciones son best-effort.
    """

    async def documento_conciliado(self, documento, org_id: str):
        """Notifica cuando un documento se concilia automaticamente"""
        monto_fmt = _formatear_monto(documento.monto)
        mensaje = (
            f"Documento conciliado automaticamente\n"
            f"- Tipo: {documento.tipo_doc or 'N/D'}\n"
            f"- Monto: {monto_fmt}\n"
            f"- Periodo: {documento.periodo or 'N/D'}\n"
            f"- Estado: {documento.estado}"
        )
        try:
            await enviar_slack(mensaje)
        except Exception as e:
            logger.warning(f"Error en notificacion documento_conciliado: {e}")

    async def documento_requiere_revision(self, documento, org_id: str):
        """Notifica cuando el OCR tuvo baja confianza y necesita revision humana"""
        confianza = float(documento.confianza_asignacion or 0)
        mensaje = (
            f"Documento requiere revision manual\n"
            f"- Archivo: {documento.nombre_original}\n"
            f"- Tipo detectado: {documento.tipo_doc or 'N/D'}\n"
            f"- Confianza OCR: {confianza:.0%}\n"
            f"- Accion: Revisar en el panel de documentos"
        )
        try:
            await enviar_slack(mensaje)
        except Exception as e:
            logger.warning(f"Error en notificacion documento_requiere_revision: {e}")

    async def error_sync_dolibarr(self, documento, error: str, org_id: str):
        """Notifica cuando falla la sincronizacion con Dolibarr"""
        mensaje = (
            f"Error en sincronizacion con Dolibarr\n"
            f"- Documento: {documento.nombre_original}\n"
            f"- Error: {error}"
        )
        try:
            await enviar_slack(mensaje)
        except Exception as e:
            logger.warning(f"Error en notificacion error_sync_dolibarr: {e}")

    async def vencimiento_proximo(self, documento, dias_restantes: int, org_id: str):
        """Notifica N dias antes del vencimiento"""
        monto_fmt = _formatear_monto(documento.monto)
        mensaje = (
            f"Vencimiento proximo ({dias_restantes} dias)\n"
            f"- Tipo: {documento.tipo_doc or 'N/D'}\n"
            f"- Monto: {monto_fmt}\n"
            f"- Vence: {documento.fecha_vencimiento}\n"
            f"- Estado: {documento.estado}"
        )
        try:
            await enviar_slack(mensaje)
        except Exception as e:
            logger.warning(f"Error en notificacion vencimiento_proximo: {e}")


notificaciones = ServicioNotificaciones()
