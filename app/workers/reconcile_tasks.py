# Tarea Celery de conciliacion bancaria automatica (cada 6 horas via beat)
import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.workers.celery_app import app_celery
from app.core.database import SessionLocal
from app.modules.documents.models import DocumentoImpositivo, MovimientoBancario
from app.modules.auth.models import Organizacion
from app.modules.reconciliation.state_machine import (
    EstadoDocumento,
    transicionar_y_registrar,
)
from app.modules.reconciliation.service import calcular_score, clasificar_confianza


# Umbrales segun spec
UMBRAL_AUTO = 0.85
UMBRAL_SUGERENCIA = 0.65


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


async def _conciliar_org_async(org_id) -> dict:
    """Concilia movimientos bancarios contra documentos SINCRONIZADOS de una organizacion."""
    resumen = {"conciliados": 0, "sugerencias": 0, "movimientos_evaluados": 0}

    async with SessionLocal() as db:
        try:
            # 1) Cargar movimientos no conciliados
            r_mov = await db.execute(
                select(MovimientoBancario).where(
                    MovimientoBancario.org_id == org_id,
                    MovimientoBancario.conciliado == False,  # noqa: E712
                )
            )
            movimientos = r_mov.scalars().all()
            resumen["movimientos_evaluados"] = len(movimientos)

            if not movimientos:
                return resumen

            # 2) Cargar documentos en estado SINCRONIZADO
            r_doc = await db.execute(
                select(DocumentoImpositivo).where(
                    DocumentoImpositivo.org_id == org_id,
                    DocumentoImpositivo.estado == EstadoDocumento.SINCRONIZADO.value,
                )
            )
            documentos = r_doc.scalars().all()
            if not documentos:
                return resumen

            # 3) Para cada movimiento, evaluar contra cada documento y encontrar el mejor
            for mov in movimientos:
                mejor_score = 0.0
                mejor_doc = None

                for doc in documentos:
                    sm = calcular_score(
                        monto_documento=float(doc.monto) if doc.monto is not None else None,
                        fecha_documento=doc.fecha_vencimiento,
                        cuit_documento=doc.cuit,
                        codigo_impuesto=doc.codigo_impuesto,
                        monto_banco=float(mov.monto),
                        fecha_banco=mov.fecha_movimiento,
                        descripcion_banco=mov.descripcion or "",
                    )
                    if sm.score > mejor_score:
                        mejor_score = sm.score
                        mejor_doc = doc

                if mejor_doc is None:
                    continue

                if mejor_score >= UMBRAL_AUTO:
                    # Auto-conciliacion + transicion a PAGADO
                    mov.conciliado = True
                    mov.conciliado_en = datetime.now(timezone.utc)
                    mov.documento_id = mejor_doc.id
                    mov.confianza_match = clasificar_confianza(mejor_score)
                    mov.score_match = Decimal(str(round(mejor_score, 4)))
                    try:
                        await transicionar_y_registrar(
                            documento=mejor_doc,
                            destino=EstadoDocumento.PAGADO,
                            actor_id=None,
                            tipo_actor="SISTEMA",
                            db=db,
                            detalle=f"Auto-conciliacion score={mejor_score:.2f}",
                        )
                    except Exception:
                        pass
                    resumen["conciliados"] += 1
                    # Notificar conciliacion automatica
                    try:
                        from app.modules.notifications.service import notificaciones
                        await notificaciones.documento_conciliado(mejor_doc, str(mejor_doc.org_id))
                    except Exception:
                        pass
                elif mejor_score >= UMBRAL_SUGERENCIA:
                    # Solo guardar sugerencia sin conciliar
                    mov.documento_id = mejor_doc.id
                    mov.confianza_match = clasificar_confianza(mejor_score)
                    mov.score_match = Decimal(str(round(mejor_score, 4)))
                    resumen["sugerencias"] += 1

            await db.commit()
        except Exception:
            await db.rollback()
            raise

    return resumen


async def _conciliar_todas_async() -> dict:
    """Recorre todas las organizaciones y dispara la conciliacion para cada una."""
    resumen_total = {"organizaciones": 0, "conciliados": 0, "sugerencias": 0}

    async with SessionLocal() as db:
        r = await db.execute(select(Organizacion))
        orgs = r.scalars().all()

    for org in orgs:
        try:
            res = await _conciliar_org_async(org.id)
            resumen_total["organizaciones"] += 1
            resumen_total["conciliados"] += res.get("conciliados", 0)
            resumen_total["sugerencias"] += res.get("sugerencias", 0)
        except Exception:
            continue

    return resumen_total


@app_celery.task(name="app.workers.reconcile_tasks.conciliar_todas_las_orgs")
def conciliar_todas_las_orgs() -> dict:
    """Task Celery programada (cada 6h): concilia movimientos bancarios de todas las orgs."""
    return _ejecutar_async(_conciliar_todas_async())


@app_celery.task(name="app.workers.reconcile_tasks.conciliar_org")
def conciliar_org(org_id: str) -> dict:
    """Task Celery disparada manualmente: concilia movimientos de una organizacion."""
    import uuid as _uuid
    return _ejecutar_async(_conciliar_org_async(_uuid.UUID(org_id)))
