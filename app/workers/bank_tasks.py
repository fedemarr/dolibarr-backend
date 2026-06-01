# Tareas Celery para procesamiento de movimientos bancarios
import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal

from app.workers.celery_app import app_celery
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)


def _ejecutar_async(coro):
    """Wrapper seguro para correr código async desde Celery en Python 3.14."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()
            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        finally:
            loop.close()
            asyncio.set_event_loop(None)


async def _conciliar_facturas_clientes_async(org_id: str, movimiento_ids: list[str]) -> dict:
    """
    Para cada crédito bancario recién importado, busca en Dolibarr si hay
    una factura pendiente que coincida y la marca como pagada automáticamente.
    """
    from sqlalchemy import select
    from app.modules.documents.models import MovimientoBancario
    from app.modules.dolibarr.client import ClienteDolibarr
    from app.modules.dolibarr.invoices import obtener_facturas_pendientes, registrar_pago_factura
    from app.modules.dolibarr.invoice_matcher import calcular_score_factura, clasificar_confianza_factura
    import uuid

    resumen = {"procesados": 0, "auto_pagados": 0, "sugerencias": 0, "errores": 0}

    async with SessionLocal() as db:
        # Cargar solo los movimientos de crédito recién importados
        ids_uuid = [uuid.UUID(mid) for mid in movimiento_ids]
        r = await db.execute(
            select(MovimientoBancario).where(
                MovimientoBancario.id.in_(ids_uuid),
                MovimientoBancario.tipo_movimiento == "CREDITO",
            )
        )
        creditos = r.scalars().all()

        if not creditos:
            return resumen

        # Obtener facturas pendientes de Dolibarr
        async with ClienteDolibarr() as cliente:
            facturas = await obtener_facturas_pendientes(cliente)

        if not facturas:
            logger.info("[BANK] No hay facturas pendientes en Dolibarr")
            return resumen

        logger.info(f"[BANK] Procesando {len(creditos)} créditos contra {len(facturas)} facturas pendientes")

        for credito in creditos:
            resumen["procesados"] += 1
            mejor_score = 0.0
            mejor_factura = None
            mejor_desglose = {}

            for factura in facturas:
                try:
                    monto_factura = float(factura.get("montttc") or factura.get("total_ttc") or 0)
                    nombre_tercero = factura.get("socnom") or factura.get("nom") or ""
                    fecha_factura_str = factura.get("date") or factura.get("datef") or ""

                    # Parsear fecha de factura
                    fecha_factura = None
                    if fecha_factura_str:
                        try:
                            from datetime import date
                            ts = int(fecha_factura_str)
                            fecha_factura = datetime.fromtimestamp(ts).date()
                        except Exception:
                            pass

                    score, desglose = calcular_score_factura(
                        monto_banco=float(credito.monto),
                        descripcion_banco=credito.descripcion or "",
                        fecha_banco=credito.fecha_movimiento,
                        monto_factura=monto_factura,
                        nombre_tercero=nombre_tercero,
                        fecha_factura=fecha_factura,
                    )

                    if score > mejor_score:
                        mejor_score = score
                        mejor_factura = factura
                        mejor_desglose = desglose
                except Exception as e:
                    logger.warning(f"[BANK] Error evaluando factura: {e}")
                    continue

            if not mejor_factura:
                continue

            confianza = clasificar_confianza_factura(mejor_score)
            factura_id = int(mejor_factura.get("id") or 0)
            factura_ref = mejor_factura.get("ref") or str(factura_id)

            if mejor_score >= 0.80:
                # Auto-pagar la factura en Dolibarr
                logger.info(f"[BANK] Auto-pagando factura {factura_ref} (score={mejor_score:.2f})")
                async with ClienteDolibarr() as cliente:
                    resultado = await registrar_pago_factura(
                        cliente=cliente,
                        id_factura=factura_id,
                        monto=float(credito.monto),
                        fecha=credito.fecha_movimiento.strftime("%Y-%m-%d"),
                        cuenta_bancaria=credito.cuenta_bancaria,
                        nota=f"Pago automático detectado en extracto bancario — {credito.descripcion}",
                    )

                if resultado is not None:
                    # Marcar movimiento bancario como conciliado
                    credito.conciliado = True
                    credito.conciliado_en = datetime.now(timezone.utc)
                    credito.confianza_match = confianza
                    credito.score_match = Decimal(str(round(mejor_score, 4)))
                    resumen["auto_pagados"] += 1
                    logger.info(f"[BANK] Factura {factura_ref} marcada como pagada en Dolibarr ✅")
                else:
                    logger.warning(f"[BANK] No se pudo registrar pago en Dolibarr para factura {factura_ref}")
                    resumen["errores"] += 1

            elif mejor_score >= 0.60:
                # Guardar sugerencia sin pagar automáticamente
                credito.confianza_match = confianza
                credito.score_match = Decimal(str(round(mejor_score, 4)))
                resumen["sugerencias"] += 1
                logger.info(f"[BANK] Sugerencia de match para factura {factura_ref} (score={mejor_score:.2f})")

        await db.commit()

    return resumen


@app_celery.task(name="app.workers.bank_tasks.conciliar_facturas_clientes")
def conciliar_facturas_clientes(org_id: str, movimiento_ids: list) -> dict:
    """
    Task Celery: cuando se importan créditos bancarios, busca facturas pendientes
    en Dolibarr y las marca como pagadas si hay match.
    """
    logger.info(f"[BANK] Iniciando conciliación de facturas para org {org_id}, {len(movimiento_ids)} movimientos")
    resultado = _ejecutar_async(_conciliar_facturas_clientes_async(org_id, movimiento_ids))
    logger.info(f"[BANK] Resultado: {resultado}")
    return resultado


@app_celery.task(name="app.workers.bank_tasks.importar_movimientos_bancarios")
def importar_movimientos_bancarios(*args, **kwargs) -> dict:
    """Placeholder — la importación se hace via API REST, no por esta task."""
    return {"estado": "usar_api_rest", "mensaje": "Importar via POST /api/v1/bancario/importar"}


async def _sincronizar_movimientos_dolibarr_async(
    org_id: str,
    movimiento_ids: list[str],
) -> dict:
    """
    Para cada movimiento bancario importado, crea el registro
    correspondiente en Dolibarr con la cuenta contable correcta.
    Este es el proceso que el cliente hacía a mano (los 3000 registros).
    """
    from sqlalchemy import select
    from app.modules.documents.models import MovimientoBancario
    from app.modules.dolibarr.client import ClienteDolibarr
    from app.modules.banking.reglas_galicia import clasificar_movimiento
    import uuid

    resumen = {"procesados": 0, "creados_en_dolibarr": 0, "errores": 0}

    async with SessionLocal() as db:
        ids_uuid = [uuid.UUID(mid) for mid in movimiento_ids]
        r = await db.execute(
            select(MovimientoBancario).where(
                MovimientoBancario.id.in_(ids_uuid)
            )
        )
        movimientos = r.scalars().all()

        async with ClienteDolibarr() as cliente:
            for mov in movimientos:
                resumen["procesados"] += 1
                try:
                    regla = clasificar_movimiento(
                        mov.descripcion or "",
                        mov.tipo_movimiento or "DEBITO",
                    )
                    monto = float(mov.monto)
                    resultado = await cliente.crear_movimiento_bancario({
                        "bankaccount_id": 1,
                        "date": mov.fecha_movimiento.strftime("%Y-%m-%d"),
                        "label": mov.descripcion or "Sin descripción",
                        "amount": monto,
                        "account_number": regla["codigo_cuenta"],
                        "num_chq": mov.referencia or "",
                    })
                    if resultado is not None:
                        resumen["creados_en_dolibarr"] += 1
                        logger.info(
                            f"[BANK] Movimiento creado en Dolibarr: "
                            f"{mov.descripcion} → {regla['codigo_cuenta']} "
                            f"({regla['nombre_cuenta']})"
                        )
                    else:
                        resumen["errores"] += 1
                except Exception as e:
                    logger.warning(f"[BANK] Error: {e}")
                    resumen["errores"] += 1

    return resumen


@app_celery.task(name="app.workers.bank_tasks.sincronizar_movimientos_dolibarr")
def sincronizar_movimientos_dolibarr(org_id: str, movimiento_ids: list) -> dict:
    """Task: crea movimientos bancarios en Dolibarr con cuentas contables automáticas."""
    return _ejecutar_async(
        _sincronizar_movimientos_dolibarr_async(org_id, movimiento_ids)
    )
