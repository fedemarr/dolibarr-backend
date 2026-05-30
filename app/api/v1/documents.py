# Endpoints REST para gestion de documentos impositivos
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ErrorApp
from app.core.limiter import limiter
from app.modules.auth.service import obtener_usuario_actual
from app.modules.auth.models import Usuario
from app.modules.documents import service, repository
from app.modules.documents.schemas import FiltrosDocumento, SolicitudAprobar


router = APIRouter(prefix="/api/v1/documentos")


def _serializar_documento(doc) -> dict:
    """Convierte un DocumentoImpositivo en dict listo para JSON."""
    return {
        "id": str(doc.id),
        "org_id": str(doc.org_id),
        "nombre_original": doc.nombre_original,
        "tipo_doc": doc.tipo_doc,
        "estado": doc.estado,
        "cuit": doc.cuit,
        "periodo": doc.periodo,
        "fecha_vencimiento": doc.fecha_vencimiento.isoformat() if doc.fecha_vencimiento else None,
        "monto": float(doc.monto) if doc.monto is not None else None,
        "codigo_impuesto": doc.codigo_impuesto,
        "concepto": doc.concepto,
        "codigo_cuenta": doc.codigo_cuenta,
        "nombre_cuenta": doc.nombre_cuenta,
        "confianza_asignacion": float(doc.confianza_asignacion) if doc.confianza_asignacion is not None else None,
        "id_factura_doli": doc.id_factura_doli,
        "detalle_error": doc.detalle_error,
        "creado_en": doc.creado_en.isoformat() if doc.creado_en else None,
        "actualizado_en": doc.actualizado_en.isoformat() if doc.actualizado_en else None,
    }


def _serializar_resumido(doc) -> dict:
    return {
        "id": str(doc.id),
        "nombre_original": doc.nombre_original,
        "tipo_doc": doc.tipo_doc,
        "estado": doc.estado,
        "monto": float(doc.monto) if doc.monto is not None else None,
        "periodo": doc.periodo,
        "creado_en": doc.creado_en.isoformat() if doc.creado_en else None,
    }


@router.post("/subir")
@limiter.limit("20/minute")
async def subir(
    request: Request,
    archivo: UploadFile = File(...),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Sube un PDF y lo encola para procesamiento async."""
    documento = await service.subir_pdf(archivo, usuario.org_id, db)
    return {"exito": True, "datos": _serializar_documento(documento)}


@router.get("")
async def listar(
    estado: str | None = Query(default=None),
    tipo_doc: str | None = Query(default=None),
    periodo: str | None = Query(default=None),
    cuit: str | None = Query(default=None),
    pagina: int = Query(default=1, ge=1),
    limite: int = Query(default=20, ge=1, le=100),
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Lista documentos paginados con filtros opcionales."""
    filtros = FiltrosDocumento(
        estado=estado, tipo_doc=tipo_doc, periodo=periodo, cuit=cuit,
        pagina=pagina, limite=limite,
    )
    items, total = await repository.listar_paginado(filtros, usuario.org_id, db)
    return {
        "exito": True,
        "datos": [_serializar_resumido(d) for d in items],
        "meta": {"pagina": pagina, "total": total, "limite": limite},
    }


@router.get("/{id}")
async def detalle(
    id: uuid.UUID,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Detalle completo de un documento."""
    doc = await repository.obtener_por_id(id, usuario.org_id, db)
    return {"exito": True, "datos": _serializar_documento(doc)}


@router.patch("/{id}/aprobar")
async def aprobar(
    id: uuid.UUID,
    correcciones: SolicitudAprobar,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Aprueba un documento (con correcciones opcionales) y encola sincronizacion con Dolibarr."""
    doc = await service.aprobar(
        id=id,
        org_id=usuario.org_id,
        correcciones=correcciones.model_dump(exclude_unset=True),
        actor_id=str(usuario.id),
        db=db,
    )
    return {"exito": True, "datos": _serializar_documento(doc)}


@router.patch("/{id}/reintentar")
async def reintentar(
    id: uuid.UUID,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Reinicia procesamiento de un documento que esta en ERROR."""
    doc = await service.reintentar(
        id=id, org_id=usuario.org_id, actor_id=str(usuario.id), db=db
    )
    return {"exito": True, "datos": _serializar_documento(doc)}


@router.get("/{id}/preview")
async def preview(
    id: uuid.UUID,
    usuario: Usuario = Depends(obtener_usuario_actual),
    db: AsyncSession = Depends(get_db),
):
    """Retorna el PDF original del documento (para visualizar en el navegador)."""
    doc = await repository.obtener_por_id(id, usuario.org_id, db)
    ruta = Path(doc.clave_s3)
    if not ruta.exists():
        raise ErrorApp(
            status_code=404,
            code="ARCHIVO_NO_ENCONTRADO",
            message="El archivo PDF no se encuentra en disco",
        )
    return FileResponse(ruta, media_type="application/pdf", filename=doc.nombre_original)
