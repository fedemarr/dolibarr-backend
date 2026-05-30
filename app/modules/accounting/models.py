# Modelo ORM para reglas contables (clasificacion de cuentas)
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Integer, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


# Lista de tipos de documento (debe coincidir con el ENUM PostgreSQL tipo_documento)
TIPOS_DOCUMENTO = (
    "VEP",
    "DECLARACION_IVA",
    "DECLARACION_GANANCIAS",
    "SUSS",
    "IIBB",
    "FACTURA_PROVEEDOR",
    "OTRO",
)


class ReglaContable(Base):
    __tablename__ = "reglas_contables"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    tipo_doc: Mapped[str | None] = mapped_column(
        SAEnum(*TIPOS_DOCUMENTO, name="tipo_documento", create_type=False),
        nullable=True,
    )
    patron_match: Mapped[dict] = mapped_column(JSONB, nullable=False)
    codigo_cuenta: Mapped[str] = mapped_column(String(20), nullable=False)
    nombre_cuenta: Mapped[str] = mapped_column(String(200), nullable=False)
    prioridad: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
