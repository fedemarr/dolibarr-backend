# Endpoints de reportes y estadisticas del sistema
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from app.core.database import get_db
from app.modules.auth.service import obtener_usuario_actual
from app.modules.documents.models import DocumentoImpositivo, LogAuditoria


router = APIRouter(prefix="/api/v1/reportes")


@router.get("/resumen")
async def resumen_periodo(
    periodo: Optional[str] = Query(None, description="Formato YYYY-MM, default mes actual"),
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Resumen estadistico de documentos para un periodo dado"""
    if not periodo:
        hoy = date.today()
        periodo = f"{hoy.year:04d}-{hoy.month:02d}"

    # Cargar documentos del periodo
    resultado = await db.execute(
        select(DocumentoImpositivo).where(
            DocumentoImpositivo.org_id == usuario.org_id,
            DocumentoImpositivo.periodo == periodo,
            DocumentoImpositivo.eliminado_en.is_(None),
        )
    )
    docs = resultado.scalars().all()

    total = len(docs)
    monto_total = sum(float(d.monto or 0) for d in docs)

    por_estado: dict = {}
    por_tipo: dict = {}
    for d in docs:
        por_estado[d.estado] = por_estado.get(d.estado, 0) + 1
        tipo = d.tipo_doc or "OTRO"
        por_tipo[tipo] = por_tipo.get(tipo, 0) + 1

    # Calcular tasa de auto-conciliacion
    conciliados = por_estado.get("RECONCILED", 0) + por_estado.get("PAID", 0)
    tasa = round(conciliados / total, 2) if total > 0 else 0.0

    # Calcular horas ahorradas (47 min por documento procesado automaticamente)
    auto_procesados_res = await db.execute(
        select(func.count(LogAuditoria.id)).where(
            LogAuditoria.org_id == usuario.org_id,
            LogAuditoria.tipo_actor == "SISTEMA",
            LogAuditoria.accion == "CAMBIO_ESTADO_CLASSIFIED",
        )
    )
    auto_procesados = auto_procesados_res.scalar() or 0
    horas_ahorradas = round((auto_procesados * 47) / 60, 1)

    return {
        "exito": True,
        "datos": {
            "periodo": periodo,
            "total_documentos": total,
            "monto_total": round(monto_total, 2),
            "por_estado": por_estado,
            "por_tipo": por_tipo,
            "tasa_auto_conciliacion": tasa,
            "horas_ahorradas_estimadas": horas_ahorradas,
        },
    }


@router.get("/vencimientos-proximos")
async def vencimientos_proximos(
    dias: int = Query(7, ge=1, le=90),
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Documentos que vencen en los proximos N dias"""
    hoy = date.today()
    limite = hoy + timedelta(days=dias)

    resultado = await db.execute(
        select(DocumentoImpositivo).where(
            DocumentoImpositivo.org_id == usuario.org_id,
            DocumentoImpositivo.fecha_vencimiento >= hoy,
            DocumentoImpositivo.fecha_vencimiento <= limite,
            DocumentoImpositivo.estado.in_(["SYNCED", "APPROVED", "CLASSIFIED"]),
            DocumentoImpositivo.eliminado_en.is_(None),
        ).order_by(DocumentoImpositivo.fecha_vencimiento.asc())
    )
    docs = resultado.scalars().all()

    return {
        "exito": True,
        "datos": [
            {
                "id": str(d.id),
                "tipo_doc": d.tipo_doc,
                "monto": float(d.monto) if d.monto else None,
                "fecha_vencimiento": d.fecha_vencimiento.isoformat(),
                "dias_restantes": (d.fecha_vencimiento - hoy).days,
                "estado": d.estado,
                "cuit": d.cuit,
                "periodo": d.periodo,
            }
            for d in docs
        ],
    }


@router.get("/actividad")
async def actividad_reciente(
    horas: int = Query(24, ge=1, le=168),
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Ultimos eventos del sistema para el feed de actividad del dashboard"""
    desde = datetime.now(timezone.utc) - timedelta(hours=horas)

    resultado = await db.execute(
        select(LogAuditoria)
        .where(
            LogAuditoria.org_id == usuario.org_id,
            LogAuditoria.creado_en >= desde,
        )
        .order_by(LogAuditoria.creado_en.desc())
        .limit(100)
    )
    registros = resultado.scalars().all()

    return {
        "exito": True,
        "datos": [
            {
                "id": r.id,
                "accion": r.accion,
                "tipo_entidad": r.tipo_entidad,
                "id_entidad": str(r.id_entidad),
                "tipo_actor": r.tipo_actor,
                "estado_nuevo": r.estado_nuevo,
                "creado_en": r.creado_en.isoformat() if r.creado_en else None,
            }
            for r in registros
        ],
    }
