# Repositorio de acceso a datos para movimientos bancarios
import uuid
from datetime import datetime, timezone, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.modules.banking.models import MovimientoBancario


async def crear_movimiento(datos: dict, org_id: uuid.UUID, db: AsyncSession) -> tuple[MovimientoBancario, bool]:
    """
    Crea un movimiento bancario si no existe ya.
    Deduplicacion por: org_id + cuenta + referencia (si hay referencia),
    o por org_id + cuenta + fecha + monto + descripcion (si no hay).
    Retorna (movimiento, es_nuevo).
    """
    referencia = datos.get("referencia")
    cuenta = datos.get("cuenta_bancaria")

    if referencia:
        resultado = await db.execute(
            select(MovimientoBancario).where(
                MovimientoBancario.org_id == org_id,
                MovimientoBancario.referencia == referencia,
                MovimientoBancario.cuenta_bancaria == cuenta,
            )
        )
        existente = resultado.scalar_one_or_none()
        if existente:
            return existente, False
    else:
        resultado = await db.execute(
            select(MovimientoBancario).where(
                MovimientoBancario.org_id == org_id,
                MovimientoBancario.fecha_movimiento == datos.get("fecha_movimiento"),
                MovimientoBancario.monto == datos.get("monto"),
                MovimientoBancario.cuenta_bancaria == cuenta,
                MovimientoBancario.descripcion == datos.get("descripcion", ""),
            )
        )
        existente = resultado.scalar_one_or_none()
        if existente:
            return existente, False

    # Quitar org_id del payload por si vino duplicado
    payload = {k: v for k, v in datos.items() if k not in ("org_id",)}

    movimiento = MovimientoBancario(
        org_id=org_id,
        **payload,
    )
    db.add(movimiento)
    await db.flush()
    return movimiento, True


async def listar_paginado(filtros, org_id: uuid.UUID, db: AsyncSession):
    """Lista movimientos con filtros opcionales y paginacion"""
    query = select(MovimientoBancario).where(MovimientoBancario.org_id == org_id)

    if filtros.conciliado is not None:
        query = query.where(MovimientoBancario.conciliado == filtros.conciliado)
    if filtros.fecha_desde:
        query = query.where(MovimientoBancario.fecha_movimiento >= filtros.fecha_desde)
    if filtros.fecha_hasta:
        query = query.where(MovimientoBancario.fecha_movimiento <= filtros.fecha_hasta)
    if filtros.cuenta:
        query = query.where(MovimientoBancario.cuenta_bancaria == filtros.cuenta)

    total_res = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_res.scalar() or 0

    offset = (filtros.pagina - 1) * filtros.limite
    query = query.offset(offset).limit(filtros.limite).order_by(MovimientoBancario.fecha_movimiento.desc())
    resultado = await db.execute(query)
    return resultado.scalars().all(), total


async def obtener_sin_conciliar(org_id: uuid.UUID, db: AsyncSession) -> list[MovimientoBancario]:
    """Retorna todos los movimientos no conciliados para el motor de conciliacion"""
    resultado = await db.execute(
        select(MovimientoBancario).where(
            MovimientoBancario.org_id == org_id,
            MovimientoBancario.conciliado == False,  # noqa: E712
        )
    )
    return resultado.scalars().all()


async def marcar_conciliado(id: uuid.UUID, documento_id: uuid.UUID, confianza: str, score: float, db: AsyncSession):
    """Marca un movimiento como conciliado"""
    resultado = await db.execute(select(MovimientoBancario).where(MovimientoBancario.id == id))
    mov = resultado.scalar_one_or_none()
    if mov:
        mov.conciliado = True
        mov.documento_id = documento_id
        mov.confianza_match = confianza
        mov.score_match = Decimal(str(round(score, 4)))
        mov.conciliado_en = datetime.now(timezone.utc)
        mov.actualizado_en = datetime.now(timezone.utc)
    return mov


async def obtener_por_id(id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession) -> MovimientoBancario:
    """Obtiene un movimiento por ID verificando org"""
    from app.core.exceptions import ErrorApp
    resultado = await db.execute(
        select(MovimientoBancario).where(
            MovimientoBancario.id == id,
            MovimientoBancario.org_id == org_id,
        )
    )
    mov = resultado.scalar_one_or_none()
    if not mov:
        raise ErrorApp(status_code=404, code="MOVIMIENTO_NO_ENCONTRADO", message="El movimiento bancario no existe")
    return mov
