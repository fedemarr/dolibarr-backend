# Tareas Celery para procesamiento de PDFs y sincronizacion con Dolibarr
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timezone

from sqlalchemy import select

from app.workers.celery_app import app_celery
from app.core.database import SessionLocal
from app.modules.documents.models import DocumentoImpositivo
from app.modules.accounting.service import procesar_documento
from app.modules.reconciliation.state_machine import (
    EstadoDocumento,
    transicionar_y_registrar,
)


# Umbral minimo de confianza para auto-clasificar sin revision humana
UMBRAL_CONFIANZA_AUTO = 0.7


def _ejecutar_async(coro):
    """
    Wrapper seguro para correr codigo async desde Celery en Python 3.14.
    Crea un event loop nuevo por cada ejecucion para evitar el error
    'Event loop is closed' que ocurre al reutilizar loops entre tasks.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            # Cancelar todas las tasks pendientes antes de cerrar
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        finally:
            loop.close()
            asyncio.set_event_loop(None)


async def _procesar_pdf_async(documento_id: str) -> None:
    """Logica principal del procesamiento (corrida desde sync Celery)."""
    doc_uuid = uuid.UUID(documento_id)

    async with SessionLocal() as db:
        try:
            # 1) Cargar documento
            resultado = await db.execute(
                select(DocumentoImpositivo).where(DocumentoImpositivo.id == doc_uuid)
            )
            documento = resultado.scalar_one_or_none()
            if documento is None:
                return

            # 2) Transicion a PROCESANDO
            await transicionar_y_registrar(
                documento=documento,
                destino=EstadoDocumento.PROCESANDO,
                actor_id=None,
                tipo_actor="SISTEMA",
                db=db,
                detalle="Inicio de procesamiento OCR",
            )
            await db.commit()

            # 3) Pipeline OCR + parsing + asignacion contable
            ruta = Path(documento.clave_s3)
            resultado_proc = await procesar_documento(
                ruta_pdf=ruta,
                org_id=str(documento.org_id),
                db=db,
            )

            # 4) Actualizar campos del documento
            for campo, valor in resultado_proc.items():
                if hasattr(documento, campo):
                    setattr(documento, campo, valor)
            documento.actualizado_en = datetime.now(timezone.utc)

            # 5) Decidir destino: CLASIFICADO o REQUIERE_REVISION
            confianza = resultado_proc.get("confianza_asignacion") or 0.0
            destino = (
                EstadoDocumento.CLASIFICADO
                if confianza >= UMBRAL_CONFIANZA_AUTO
                else EstadoDocumento.REQUIERE_REVISION
            )
            await transicionar_y_registrar(
                documento=documento,
                destino=destino,
                actor_id=None,
                tipo_actor="SISTEMA",
                db=db,
                detalle=f"Confianza={confianza:.2f}",
            )
            await db.commit()

            # Notificar si el documento requiere revision humana
            if destino == EstadoDocumento.REQUIERE_REVISION:
                try:
                    from app.modules.notifications.service import notificaciones
                    await notificaciones.documento_requiere_revision(documento, str(documento.org_id))
                except Exception:
                    pass

        except Exception as e:
            # En caso de error, transicionar a ERROR y guardar el detalle
            await db.rollback()
            try:
                async with SessionLocal() as db_err:
                    resultado = await db_err.execute(
                        select(DocumentoImpositivo).where(DocumentoImpositivo.id == doc_uuid)
                    )
                    documento = resultado.scalar_one_or_none()
                    if documento is not None:
                        documento.detalle_error = f"Error procesando PDF: {str(e)[:500]}"
                        try:
                            await transicionar_y_registrar(
                                documento=documento,
                                destino=EstadoDocumento.ERROR,
                                actor_id=None,
                                tipo_actor="SISTEMA",
                                db=db_err,
                                detalle=str(e)[:200],
                            )
                        except Exception:
                            # Si la transicion falla (estado actual no permite ERROR), forzar
                            documento.estado = "ERROR"
                        await db_err.commit()
            except Exception:
                pass


@app_celery.task(name="app.workers.pdf_tasks.procesar_pdf")
def procesar_pdf(documento_id: str) -> str:
    """Task Celery: procesa un PDF (OCR + clasificacion + asignacion contable)."""
    _ejecutar_async(_procesar_pdf_async(documento_id))
    return documento_id


async def _sincronizar_dolibarr_async(documento_id: str) -> None:
    """Crea la factura en Dolibarr a partir del documento aprobado."""
    from app.modules.dolibarr.client import ClienteDolibarr
    from app.modules.dolibarr.invoices import construir_payload_factura_proveedor

    doc_uuid = uuid.UUID(documento_id)

    async with SessionLocal() as db:
        try:
            resultado = await db.execute(
                select(DocumentoImpositivo).where(DocumentoImpositivo.id == doc_uuid)
            )
            documento = resultado.scalar_one_or_none()
            if documento is None:
                return

            fecha_factura = (
                documento.fecha_vencimiento.isoformat()
                if documento.fecha_vencimiento
                else datetime.now(timezone.utc).date().isoformat()
            )
            ref = f"AUTO-{str(documento.id)[:8]}"

            payload = construir_payload_factura_proveedor(
                ref=ref,
                monto=float(documento.monto) if documento.monto else 0.0,
                fecha_factura=fecha_factura,
                codigo_cuenta=documento.codigo_cuenta or "2.99.001",
                concepto=documento.concepto or documento.nombre_original,
                cuit=documento.cuit,
            )

            async with ClienteDolibarr() as cliente:
                respuesta = await cliente.crear_factura_proveedor(payload)

            # Dolibarr puede devolver int (id) o dict {"id": int}
            id_factura = respuesta if isinstance(respuesta, int) else (respuesta.get("id") if isinstance(respuesta, dict) else None)
            documento.id_factura_doli = id_factura

            await transicionar_y_registrar(
                documento=documento,
                destino=EstadoDocumento.SINCRONIZADO,
                actor_id=None,
                tipo_actor="SISTEMA",
                db=db,
                detalle=f"Factura Dolibarr creada id={id_factura}",
            )
            await db.commit()
        except Exception as e:
            await db.rollback()
            try:
                async with SessionLocal() as db_err:
                    resultado = await db_err.execute(
                        select(DocumentoImpositivo).where(DocumentoImpositivo.id == doc_uuid)
                    )
                    documento = resultado.scalar_one_or_none()
                    if documento is not None:
                        documento.detalle_error = f"Error sincronizando con Dolibarr: {str(e)[:500]}"
                        try:
                            await transicionar_y_registrar(
                                documento=documento,
                                destino=EstadoDocumento.ERROR,
                                actor_id=None,
                                tipo_actor="SISTEMA",
                                db=db_err,
                                detalle=str(e)[:200],
                            )
                        except Exception:
                            documento.estado = "ERROR"
                        await db_err.commit()
                        # Notificar error de sincronizacion
                        try:
                            from app.modules.notifications.service import notificaciones
                            await notificaciones.error_sync_dolibarr(documento, str(e), str(documento.org_id))
                        except Exception:
                            pass
            except Exception:
                pass


@app_celery.task(name="app.workers.pdf_tasks.sincronizar_con_dolibarr")
def sincronizar_con_dolibarr(documento_id: str) -> str:
    """Task Celery: crea la factura proveedor correspondiente en Dolibarr."""
    _ejecutar_async(_sincronizar_dolibarr_async(documento_id))
    return documento_id
