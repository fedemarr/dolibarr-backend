# Endpoints REST para gestion de reglas contables
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from datetime import datetime, timezone

from app.core.database import get_db
from app.modules.auth.service import obtener_usuario_actual
from app.modules.accounting.models import ReglaContable
from app.modules.accounting.schemas import (
    SolicitudCrearRegla, SolicitudActualizarRegla, RespuestaRegla, SolicitudReordenar,
)
from app.core.exceptions import ErrorApp


router = APIRouter(prefix="/api/v1/reglas")


def _serializar_regla(r: ReglaContable) -> dict:
    return {
        "id": str(r.id),
        "nombre": r.nombre,
        "tipo_doc": r.tipo_doc,
        "patron_match": r.patron_match,
        "codigo_cuenta": r.codigo_cuenta,
        "nombre_cuenta": r.nombre_cuenta,
        "prioridad": r.prioridad,
        "activa": r.activa,
        "creado_en": r.creado_en.isoformat() if r.creado_en else None,
    }


@router.get("")
async def listar_reglas(
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Lista todas las reglas contables de la organizacion ordenadas por prioridad"""
    resultado = await db.execute(
        select(ReglaContable)
        .where(ReglaContable.org_id == usuario.org_id)
        .order_by(ReglaContable.prioridad.asc())
    )
    reglas = resultado.scalars().all()
    return {"exito": True, "datos": [_serializar_regla(r) for r in reglas]}


@router.post("")
async def crear_regla(
    body: SolicitudCrearRegla,
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Crea una nueva regla contable para la organizacion"""
    regla = ReglaContable(
        org_id=usuario.org_id,
        nombre=body.nombre,
        tipo_doc=body.tipo_doc,
        patron_match=body.patron_match,
        codigo_cuenta=body.codigo_cuenta,
        nombre_cuenta=body.nombre_cuenta,
        prioridad=body.prioridad,
        activa=True,
        creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    )
    db.add(regla)
    await db.flush()
    return {"exito": True, "datos": _serializar_regla(regla)}


@router.put("/{id}")
async def actualizar_regla(
    id: uuid.UUID,
    body: SolicitudActualizarRegla,
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Actualiza campos de una regla contable"""
    resultado = await db.execute(
        select(ReglaContable).where(ReglaContable.id == id, ReglaContable.org_id == usuario.org_id)
    )
    regla = resultado.scalar_one_or_none()
    if not regla:
        raise ErrorApp(status_code=404, code="REGLA_NO_ENCONTRADA", message="La regla contable no existe")

    cambios = body.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(regla, campo, valor)
    regla.actualizado_en = datetime.now(timezone.utc)

    return {"exito": True, "datos": _serializar_regla(regla)}


@router.delete("/{id}")
async def eliminar_regla(
    id: uuid.UUID,
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Desactiva una regla contable (soft delete)"""
    resultado = await db.execute(
        select(ReglaContable).where(ReglaContable.id == id, ReglaContable.org_id == usuario.org_id)
    )
    regla = resultado.scalar_one_or_none()
    if not regla:
        raise ErrorApp(status_code=404, code="REGLA_NO_ENCONTRADA", message="La regla contable no existe")

    regla.activa = False
    regla.actualizado_en = datetime.now(timezone.utc)
    return {"exito": True, "datos": {"mensaje": "Regla desactivada correctamente"}}


@router.post("/reordenar")
async def reordenar_reglas(
    body: SolicitudReordenar,
    usuario=Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Reasigna prioridades a las reglas segun el orden recibido (util para drag & drop)"""
    for indice, regla_id in enumerate(body.ids_en_orden, start=1):
        resultado = await db.execute(
            select(ReglaContable).where(
                ReglaContable.id == regla_id,
                ReglaContable.org_id == usuario.org_id,
            )
        )
        regla = resultado.scalar_one_or_none()
        if regla:
            regla.prioridad = indice * 10
            regla.actualizado_en = datetime.now(timezone.utc)

    return {"exito": True, "datos": {"mensaje": f"Prioridades actualizadas para {len(body.ids_en_orden)} reglas"}}
