# Endpoints del panel de conciliacion bancaria
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import uuid

from app.core.database import get_db
from app.modules.auth.service import obtener_usuario_actual
from app.modules.banking import repository as banking_repo
from app.modules.documents.models import DocumentoImpositivo, LogAuditoria
from app.modules.reconciliation.state_machine import EstadoDocumento, transicionar_y_registrar
from app.modules.reconciliation.service import calcular_score, clasificar_confianza
from app.core.exceptions import ErrorApp


router = APIRouter(prefix="/api/v1/conciliacion")


@router.get("/pendientes")
async def obtener_pendientes(
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna movimientos sin conciliar con sus sugerencias de match ordenadas por score.
    """
    movimientos = await banking_repo.obtener_sin_conciliar(usuario.org_id, db)

    # Cargar documentos en estado SINCRONIZADO de esta org
    resultado = await db.execute(
        select(DocumentoImpositivo).where(
            DocumentoImpositivo.org_id == usuario.org_id,
            DocumentoImpositivo.estado == EstadoDocumento.SINCRONIZADO.value,
            DocumentoImpositivo.eliminado_en.is_(None),
        )
    )
    documentos = resultado.scalars().all()

    pares = []
    for mov in movimientos:
        sugerencias = []
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
            score_total = sm.score
            desglose = sm.detalle
            if score_total >= 0.40:  # umbral minimo para mostrar sugerencia
                confianza = clasificar_confianza(score_total)
                sugerencias.append({
                    "documento": {
                        "id": str(doc.id),
                        "tipo_doc": doc.tipo_doc,
                        "monto": float(doc.monto) if doc.monto else None,
                        "periodo": doc.periodo,
                        "cuit": doc.cuit,
                        "nombre_original": doc.nombre_original,
                        "fecha_vencimiento": doc.fecha_vencimiento.isoformat() if doc.fecha_vencimiento else None,
                    },
                    "score": round(score_total, 4),
                    "confianza": confianza,
                    "desglose": desglose,
                })
        sugerencias.sort(key=lambda x: x["score"], reverse=True)
        pares.append({
            "movimiento": {
                "id": str(mov.id),
                "fecha_movimiento": mov.fecha_movimiento.isoformat(),
                "monto": float(mov.monto),
                "descripcion": mov.descripcion,
                "referencia": mov.referencia,
                "tipo_movimiento": mov.tipo_movimiento,
                "cuenta_bancaria": mov.cuenta_bancaria,
            },
            "sugerencias": sugerencias[:5],  # maximo 5 sugerencias por movimiento
        })

    return {"exito": True, "datos": pares}


@router.post("/confirmar")
async def confirmar_match(
    body: dict,
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Confirma manualmente el match entre un movimiento bancario y un documento"""
    movimiento_id = uuid.UUID(str(body.get("movimiento_id", "")))
    documento_id = uuid.UUID(str(body.get("documento_id", "")))

    movimiento = await banking_repo.obtener_por_id(movimiento_id, usuario.org_id, db)

    from app.modules.documents import repository as doc_repo
    documento = await doc_repo.obtener_por_id(documento_id, usuario.org_id, db)

    if documento.estado != EstadoDocumento.SINCRONIZADO.value:
        raise ErrorApp(
            status_code=409,
            code="ESTADO_INVALIDO",
            message=f"El documento debe estar SYNCED, esta en {documento.estado}",
        )

    await banking_repo.marcar_conciliado(movimiento_id, documento_id, "MANUAL", 1.0, db)
    await transicionar_y_registrar(
        documento=documento,
        destino=EstadoDocumento.PAGADO,
        actor_id=str(usuario.id),
        tipo_actor="USUARIO",
        db=db,
        detalle="Conciliacion confirmada manualmente",
    )

    from app.modules.reconciliation.events import registrar_auditoria
    await registrar_auditoria(
        db=db,
        org_id=str(usuario.org_id),
        tipo_entidad="conciliacion",
        id_entidad=str(movimiento_id),
        accion="CONCILIACION_MANUAL",
        estado_anterior={"conciliado": False},
        estado_nuevo={"conciliado": True, "documento_id": str(documento_id)},
        actor_id=str(usuario.id),
        tipo_actor="USUARIO",
    )

    return {"exito": True, "datos": {"mensaje": "Conciliacion confirmada correctamente"}}


@router.get("/historial")
async def obtener_historial(
    limite: int = Query(50, ge=1, le=200),
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Retorna las ultimas conciliaciones (automaticas y manuales)"""
    resultado = await db.execute(
        select(LogAuditoria)
        .where(
            LogAuditoria.org_id == usuario.org_id,
            LogAuditoria.tipo_entidad == "conciliacion",
        )
        .order_by(desc(LogAuditoria.creado_en))
        .limit(limite)
    )
    registros = resultado.scalars().all()
    return {
        "exito": True,
        "datos": [
            {
                "id": r.id,
                "accion": r.accion,
                "id_entidad": str(r.id_entidad),
                "estado_nuevo": r.estado_nuevo,
                "actor_id": str(r.actor_id) if r.actor_id else None,
                "tipo_actor": r.tipo_actor,
                "creado_en": r.creado_en.isoformat() if r.creado_en else None,
            }
            for r in registros
        ],
    }
