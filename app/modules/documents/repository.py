# Repositorio de acceso a datos para documentos impositivos
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.modules.documents.models import DocumentoImpositivo
from app.core.exceptions import ErrorApp
import uuid


async def obtener_por_id(
    id: uuid.UUID, org_id: uuid.UUID, db: AsyncSession
) -> DocumentoImpositivo:
    """Obtiene un documento por ID verificando que pertenezca a la organizacion."""
    resultado = await db.execute(
        select(DocumentoImpositivo).where(
            DocumentoImpositivo.id == id,
            DocumentoImpositivo.org_id == org_id,
            DocumentoImpositivo.eliminado_en.is_(None),
        )
    )
    doc = resultado.scalar_one_or_none()
    if not doc:
        raise ErrorApp(
            status_code=404,
            code="DOCUMENTO_NO_ENCONTRADO",
            message="El documento solicitado no existe",
        )
    return doc


async def listar_paginado(filtros, org_id: uuid.UUID, db: AsyncSession):
    """Retorna (items, total) con paginacion y filtros opcionales."""
    query = select(DocumentoImpositivo).where(
        DocumentoImpositivo.org_id == org_id,
        DocumentoImpositivo.eliminado_en.is_(None),
    )
    if filtros.estado:
        query = query.where(DocumentoImpositivo.estado == filtros.estado)
    if filtros.tipo_doc:
        query = query.where(DocumentoImpositivo.tipo_doc == filtros.tipo_doc)
    if filtros.periodo:
        query = query.where(DocumentoImpositivo.periodo == filtros.periodo)
    if filtros.cuit:
        query = query.where(DocumentoImpositivo.cuit == filtros.cuit)

    total_query = select(func.count()).select_from(query.subquery())
    total_resultado = await db.execute(total_query)
    total = total_resultado.scalar() or 0

    offset = (filtros.pagina - 1) * filtros.limite
    query = (
        query.offset(offset)
        .limit(filtros.limite)
        .order_by(DocumentoImpositivo.creado_en.desc())
    )
    resultado = await db.execute(query)
    items = resultado.scalars().all()

    return items, total


async def actualizar_campos(id: uuid.UUID, campos: dict, db: AsyncSession):
    """Actualiza campos especificos de un documento."""
    from datetime import datetime, timezone
    if not campos:
        return
    campos["actualizado_en"] = datetime.now(timezone.utc)
    await db.execute(
        DocumentoImpositivo.__table__.update()
        .where(DocumentoImpositivo.id == id)
        .values(**campos)
    )
