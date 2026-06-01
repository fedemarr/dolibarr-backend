# Servicio de negocio para documentos impositivos
import uuid
import base64
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ErrorApp
from app.modules.documents.models import DocumentoImpositivo
from app.modules.documents import repository


async def subir_pdf(
    archivo: UploadFile,
    org_id: uuid.UUID,
    db: AsyncSession,
) -> DocumentoImpositivo:
    """
    Valida que sea un PDF, guarda el contenido en la DB y encola en Celery.
    El contenido se guarda en datos_ocr_raw para que el worker pueda accederlo
    sin necesidad de compartir filesystem entre contenedores.
    """
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

    contenido = await archivo.read()

    # Limitar tamaño a 10MB
    if len(contenido) > 10 * 1024 * 1024:
        raise ErrorApp(
            status_code=400,
            code="ARCHIVO_DEMASIADO_GRANDE",
            message="El archivo supera el tamaño máximo de 10 MB",
        )

    doc_id = uuid.uuid4()

    # Guardar contenido del PDF en base64 dentro de datos_ocr_raw
    # Esto permite que el worker acceda al PDF sin compartir filesystem
    pdf_b64 = base64.b64encode(contenido).decode("utf-8")

    documento = DocumentoImpositivo(
        id=doc_id,
        org_id=org_id,
        nombre_original=archivo.filename,
        clave_s3=f"db:{doc_id}",  # indica que el contenido esta en la DB
        estado="UPLOADED",
        datos_ocr_raw={"pdf_base64": pdf_b64},
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
