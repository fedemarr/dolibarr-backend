# Registro de eventos de auditoria (insercion en tabla log_auditoria)
import uuid
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.documents.models import LogAuditoria


async def registrar_auditoria(
    db: AsyncSession,
    org_id: str,
    tipo_entidad: str,
    id_entidad: str,
    accion: str,
    estado_anterior: Optional[dict] = None,
    estado_nuevo: Optional[dict] = None,
    actor_id: Optional[str] = None,
    tipo_actor: Optional[str] = None,
) -> None:
    """Inserta una entrada en la tabla log_auditoria (solo-escritura)."""
    entrada = LogAuditoria(
        org_id=uuid.UUID(org_id) if isinstance(org_id, str) else org_id,
        tipo_entidad=tipo_entidad,
        id_entidad=uuid.UUID(id_entidad) if isinstance(id_entidad, str) else id_entidad,
        accion=accion,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        actor_id=uuid.UUID(actor_id) if isinstance(actor_id, str) and actor_id else (actor_id if not isinstance(actor_id, str) else None),
        tipo_actor=tipo_actor,
    )
    db.add(entrada)
    await db.flush()
