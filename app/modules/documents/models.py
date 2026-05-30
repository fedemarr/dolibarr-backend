# Modelo ORM para documentos impositivos (VEP, DJ IVA, SUSS, IIBB, etc.)
import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import (
    String, Boolean, DateTime, Date, Integer, Numeric, Text, ForeignKey, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.core.database import Base


TIPOS_DOCUMENTO = (
    "VEP",
    "DECLARACION_IVA",
    "DECLARACION_GANANCIAS",
    "SUSS",
    "IIBB",
    "FACTURA_PROVEEDOR",
    "OTRO",
)

ESTADOS_DOCUMENTO = (
    "UPLOADED",
    "PROCESSING",
    "CLASSIFIED",
    "PENDING_REVIEW",
    "APPROVED",
    "SYNCED",
    "PAID",
    "RECONCILED",
    "ERROR",
)


class DocumentoImpositivo(Base):
    __tablename__ = "documentos_impositivos"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False, index=True)
    nombre_original: Mapped[str] = mapped_column(String(255), nullable=False)
    clave_s3: Mapped[str] = mapped_column(String(500), nullable=False)
    tipo_doc: Mapped[str | None] = mapped_column(
        SAEnum(*TIPOS_DOCUMENTO, name="tipo_documento", create_type=False),
        nullable=True,
    )
    estado: Mapped[str] = mapped_column(
        SAEnum(*ESTADOS_DOCUMENTO, name="estado_documento", create_type=False),
        default="UPLOADED",
        nullable=False,
    )
    cuit: Mapped[str | None] = mapped_column(String(13), nullable=True)
    periodo: Mapped[str | None] = mapped_column(String(7), nullable=True)
    fecha_vencimiento: Mapped[date | None] = mapped_column(Date, nullable=True)
    monto: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    codigo_impuesto: Mapped[str | None] = mapped_column(String(50), nullable=True)
    concepto: Mapped[str | None] = mapped_column(Text, nullable=True)
    codigo_cuenta: Mapped[str | None] = mapped_column(String(20), nullable=True)
    nombre_cuenta: Mapped[str | None] = mapped_column(String(200), nullable=True)
    regla_asignacion: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confianza_asignacion: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    id_factura_doli: Mapped[int | None] = mapped_column(Integer, nullable=True)
    id_pago_doli: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url_objeto_doli: Mapped[str | None] = mapped_column(Text, nullable=True)
    datos_ocr_raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    log_procesamiento: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    detalle_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    revisado_por: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    revisado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    eliminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class MovimientoBancario(Base):
    __tablename__ = "movimientos_bancarios"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    cuenta_bancaria: Mapped[str] = mapped_column(String(50), nullable=False)
    fecha_movimiento: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_valor: Mapped[date | None] = mapped_column(Date, nullable=True)
    monto: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    descripcion: Mapped[str | None] = mapped_column(Text, nullable=True)
    referencia: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tipo_movimiento: Mapped[str | None] = mapped_column(String(10), nullable=True)
    datos_raw: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    conciliado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    conciliado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    documento_id: Mapped[uuid.UUID | None] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("documentos_impositivos.id"), nullable=True
    )
    confianza_match: Mapped[str | None] = mapped_column(
        SAEnum("HIGH", "MEDIUM", "LOW", "MANUAL", name="confianza_match", create_type=False),
        nullable=True,
    )
    score_match: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class LogAuditoria(Base):
    __tablename__ = "log_auditoria"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    org_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    tipo_entidad: Mapped[str] = mapped_column(String(50), nullable=False)
    id_entidad: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    accion: Mapped[str] = mapped_column(String(50), nullable=False)
    estado_anterior: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    estado_nuevo: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    tipo_actor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
