# Servicio de negocio para documentos impositivos
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorApp
from app.modules.documents.models import DocumentoImpositivo
from app.modules.documents import repository


# Directorio local donde se guardan los PDFs (en produccion seria S3)
DIRECTORIO_PDFS = Path("C:/tmp/dolibarr_pdfs")


async def subir_pdf(
    archivo: UploadFile,
    org_id: uuid.UUID,
    db: AsyncSession,
) -> DocumentoImpositivo:
    """
    Valida que sea un PDF, guarda en disco local, crea registro en DB y encola en Celery.
    """
    # Validar tipo de archivo por extension y content_type
    if not archivo.filename or not archivo.filename.lower().endswith(".pdf"):
        raise ErrorApp(
            status_code=400,
            code="ARCHIVO_INVALIDO",
            message="Solo se aceptan archivos PDF",
        )
    if archivo.content_type and "pdf" not in archivo.content_type.lower():
        raise ErrorApp(
            status_code=400,
            code="ARCHIVO_INVALIDO",
            message="El archivo debe ser un PDF valido",
        )

    # Crear directorio si no existe
    DIRECTORIO_PDFS.mkdir(parents=True, exist_ok=True)

    # Generar nombre unico para el archivo
    doc_id = uuid.uuid4()
    nombre_archivo = f"{doc_id}.pdf"
    ruta_local = DIRECTORIO_PDFS / nombre_archivo

    # Guardar archivo en disco
    contenido = await archivo.read()
    with open(ruta_local, "wb") as f:
        f.write(contenido)

    # Crear registro en base de datos
    documento = DocumentoImpositivo(
        id=doc_id,
        org_id=org_id,
        nombre_original=archivo.filename,
        clave_s3=str(ruta_local),
        estado="UPLOADED",
        log_procesamiento=[],
        creado_en=datetime.now(timezone.utc),
        actualizado_en=datetime.now(timezone.utc),
    )
    db.add(documento)
    await db.flush()

    # Encolar procesamiento en Celery
    try:
        from app.workers.pdf_tasks import procesar_pdf
        procesar_pdf.delay(str(doc_id))
    except Exception:
        # Si Celery/Redis no esta disponible, el documento queda en UPLOADED
        pass

    return documento


async def aprobar(
    id: uuid.UUID,
    org_id: uuid.UUID,
    correcciones: dict,
    actor_id: str,
    db: AsyncSession,
):
    """Aprueba un documento (con correcciones opcionales) y encola la sincronizacion con Dolibarr."""
    from app.modules.reconciliation.state_machine import (
        EstadoDocumento,
        transicionar_y_registrar,
    )

    documento = await repository.obtener_por_id(id, org_id, db)

    if correcciones:
        # Filtrar None
        correcciones_limpias = {k: v for k, v in correcciones.items() if v is not None}
        if correcciones_limpias:
            await repository.actualizar_campos(id, correcciones_limpias, db)
            await db.refresh(documento)

    await transicionar_y_registrar(
        documento=documento,
        destino=EstadoDocumento.APROBADO,
        actor_id=actor_id,
        tipo_actor="USUARIO",
        db=db,
        detalle="Aprobado por operador",
    )

    # Encolar sincronizacion con Dolibarr
    try:
        from app.workers.pdf_tasks import sincronizar_con_dolibarr
        sincronizar_con_dolibarr.delay(str(id))
    except Exception:
        pass

    return documento


async def reintentar(id: uuid.UUID, org_id: uuid.UUID, actor_id: str, db: AsyncSession):
    """Reinicia el procesamiento de un documento que esta en ERROR."""
    from app.modules.reconciliation.state_machine import (
        EstadoDocumento,
        transicionar_y_registrar,
    )

    documento = await repository.obtener_por_id(id, org_id, db)

    await transicionar_y_registrar(
        documento=documento,
        destino=EstadoDocumento.SUBIDO,
        actor_id=actor_id,
        tipo_actor="USUARIO",
        db=db,
        detalle="Reintento manual",
    )

    await repository.actualizar_campos(id, {"detalle_error": None}, db)

    try:
        from app.workers.pdf_tasks import procesar_pdf
        procesar_pdf.delay(str(id))
    except Exception:
        pass

    return documento
