# Endpoints REST para el modulo bancario
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import date
import uuid

from app.core.database import get_db
from app.modules.auth.service import obtener_usuario_actual
from app.modules.banking import service as banking_service
from app.modules.banking import repository as banking_repo
from app.modules.banking.schemas import FiltrosMovimiento, RespuestaMovimiento
from app.modules.reconciliation.state_machine import EstadoDocumento, transicionar_y_registrar
from app.modules.documents import repository as doc_repo
from app.core.exceptions import ErrorApp


router = APIRouter(prefix="/api/v1/bancario")


@router.post("/importar")
async def importar_extracto(
    archivo: UploadFile = File(...),
    cuenta_bancaria: str = Form(...),
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Importa un extracto bancario (CSV u OFX) y crea los movimientos en la DB"""
    contenido = await archivo.read()
    nombre = (archivo.filename or "").lower()
    formato = "ofx" if nombre.endswith((".ofx", ".qfx")) else "csv"

    resultado = await banking_service.importar_archivo(
        contenido=contenido,
        formato=formato,
        cuenta=cuenta_bancaria,
        org_id=usuario.org_id,
        db=db,
    )
    return {"exito": True, "datos": resultado}


@router.get("/facturas-pendientes")
async def obtener_facturas_pendientes_dolibarr(
    usuario=Depends(obtener_usuario_actual),
):
    """
    Retorna las facturas a clientes pendientes de pago directamente desde Dolibarr.
    Útil para ver qué facturas están esperando cobro.
    """
    from app.modules.dolibarr.client import ClienteDolibarr
    from app.modules.dolibarr.invoices import obtener_facturas_pendientes

    try:
        async with ClienteDolibarr() as cliente:
            facturas = await obtener_facturas_pendientes(cliente)
        return {
            "exito": True,
            "datos": [
                {
                    "id": f.get("id"),
                    "ref": f.get("ref"),
                    "tercero": f.get("socnom") or f.get("nom"),
                    "monto": float(f.get("montttc") or f.get("total_ttc") or 0),
                    "fecha": f.get("date"),
                    "estado": f.get("statut"),
                }
                for f in facturas[:100]
            ],
            "meta": {"total": len(facturas)},
        }
    except Exception as e:
        return {"exito": False, "error": {"codigo": "ERROR_DOLIBARR", "mensaje": str(e)}}


@router.get("/movimientos")
async def listar_movimientos(
    conciliado: Optional[bool] = Query(None),
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    cuenta: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    limite: int = Query(50, ge=1, le=200),
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Lista movimientos bancarios con filtros opcionales y paginacion"""
    filtros = FiltrosMovimiento(
        conciliado=conciliado,
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cuenta=cuenta,
        pagina=pagina,
        limite=limite,
    )
    items, total = await banking_repo.listar_paginado(filtros, usuario.org_id, db)
    return {
        "exito": True,
        "datos": [RespuestaMovimiento.model_validate(i).model_dump(mode="json") for i in items],
        "meta": {"pagina": pagina, "total": total, "limite": limite},
    }


@router.get("/movimientos/{id}")
async def obtener_movimiento(
    id: uuid.UUID,
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el detalle de un movimiento bancario"""
    mov = await banking_repo.obtener_por_id(id, usuario.org_id, db)
    return {"exito": True, "datos": RespuestaMovimiento.model_validate(mov).model_dump(mode="json")}


@router.post("/conciliar")
async def disparar_conciliacion(
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Dispara manualmente la tarea de conciliacion automatica para la organizacion"""
    # Intentar despachar via Celery; si no, ejecutar sincronicamente
    try:
        from app.workers.reconcile_tasks import conciliar_org
        task = conciliar_org.delay(str(usuario.org_id))
        return {"exito": True, "datos": {"mensaje": "Conciliacion iniciada en segundo plano", "task_id": task.id}}
    except Exception:
        # Fallback: ejecutar la logica async directamente
        from app.workers.reconcile_tasks import _conciliar_org_async
        try:
            resultado = await _conciliar_org_async(usuario.org_id)
            return {"exito": True, "datos": resultado}
        except Exception as e:
            return {"exito": False, "datos": {"mensaje": f"No se pudo ejecutar conciliacion: {e}"}}


@router.patch("/movimientos/{id}/match")
async def asignar_match_manual(
    id: uuid.UUID,
    body: dict,
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Asigna manualmente un movimiento bancario a un documento impositivo"""
    documento_id = uuid.UUID(str(body.get("documento_id", "")))

    # Verificar que el movimiento existe y pertenece a la org
    movimiento = await banking_repo.obtener_por_id(id, usuario.org_id, db)

    # Verificar que el documento existe y pertenece a la org
    documento = await doc_repo.obtener_por_id(documento_id, usuario.org_id, db)

    # Verificar que el documento esta en estado valido para match
    estados_validos = {EstadoDocumento.SINCRONIZADO.value, EstadoDocumento.APROBADO.value}
    if documento.estado not in estados_validos:
        raise ErrorApp(
            status_code=409,
            code="ESTADO_INVALIDO",
            message=f"El documento debe estar en estado SYNCED o APPROVED, esta en {documento.estado}",
        )

    # Marcar movimiento como conciliado
    await banking_repo.marcar_conciliado(id, documento_id, "MANUAL", 1.0, db)

    # Si el documento esta SYNCED transicionarlo a PAGADO
    if documento.estado == EstadoDocumento.SINCRONIZADO.value:
        await transicionar_y_registrar(
            documento=documento,
            destino=EstadoDocumento.PAGADO,
            actor_id=str(usuario.id),
            tipo_actor="USUARIO",
            db=db,
            detalle="Match manual por operador",
        )

    await db.refresh(movimiento)
    return {"exito": True, "datos": RespuestaMovimiento.model_validate(movimiento).model_dump(mode="json")}
