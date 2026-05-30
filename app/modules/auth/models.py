# Modelos ORM para autenticacion: Organizacion y Usuario
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Organizacion(Base):
    __tablename__ = "organizaciones"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    cuit: Mapped[str | None] = mapped_column(String(13), nullable=True)
    zona_horaria: Mapped[str] = mapped_column(
        String(50), default="America/Argentina/Buenos_Aires", nullable=False
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relaciones inversas
    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="organizacion")


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    org_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("organizaciones.id"), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    # Se usa el tipo ENUM ya creado en la migration. create_type=False evita que SQLAlchemy intente recrearlo.
    rol: Mapped[str] = mapped_column(
        SAEnum("ADMIN", "OPERATOR", name="rol_usuario", create_type=False),
        default="OPERATOR",
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    eliminado_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organizacion: Mapped[Organizacion] = relationship(back_populates="usuarios")
