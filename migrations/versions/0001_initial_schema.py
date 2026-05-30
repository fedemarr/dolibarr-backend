"""Esquema inicial: enums, organizaciones, usuarios, documentos, movimientos bancarios,
reglas contables y log de auditoria.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# Identificadores de revision
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) Crear extension pgcrypto para gen_random_uuid()
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # 2) Crear los tipos ENUM nativos de PostgreSQL
    op.execute(
        "CREATE TYPE tipo_documento AS ENUM ("
        "'VEP','DECLARACION_IVA','DECLARACION_GANANCIAS','SUSS','IIBB','FACTURA_PROVEEDOR','OTRO');"
    )
    op.execute(
        "CREATE TYPE estado_documento AS ENUM ("
        "'UPLOADED','PROCESSING','CLASSIFIED','PENDING_REVIEW','APPROVED','SYNCED','PAID','RECONCILED','ERROR');"
    )
    op.execute("CREATE TYPE confianza_match AS ENUM ('HIGH','MEDIUM','LOW','MANUAL');")
    op.execute("CREATE TYPE rol_usuario AS ENUM ('ADMIN','OPERATOR');")

    # 3) Tabla organizaciones
    op.create_table(
        "organizaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column("cuit", sa.String(13), nullable=True),
        sa.Column("zona_horaria", sa.String(50), server_default="America/Argentina/Buenos_Aires", nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 4) Tabla usuarios
    op.create_table(
        "usuarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizaciones.id"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("nombre", sa.String(100), nullable=False),
        sa.Column(
            "rol",
            postgresql.ENUM("ADMIN", "OPERATOR", name="rol_usuario", create_type=False),
            server_default="OPERATOR",
            nullable=False,
        ),
        sa.Column("activo", sa.Boolean, server_default=sa.text("TRUE"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("eliminado_en", sa.DateTime(timezone=True), nullable=True),
    )

    # 5) Tabla documentos_impositivos
    op.create_table(
        "documentos_impositivos",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre_original", sa.String(255), nullable=False),
        sa.Column("clave_s3", sa.String(500), nullable=False),
        sa.Column(
            "tipo_doc",
            postgresql.ENUM(
                "VEP", "DECLARACION_IVA", "DECLARACION_GANANCIAS", "SUSS", "IIBB", "FACTURA_PROVEEDOR", "OTRO",
                name="tipo_documento", create_type=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "estado",
            postgresql.ENUM(
                "UPLOADED", "PROCESSING", "CLASSIFIED", "PENDING_REVIEW", "APPROVED",
                "SYNCED", "PAID", "RECONCILED", "ERROR",
                name="estado_documento", create_type=False,
            ),
            server_default="UPLOADED",
            nullable=False,
        ),
        sa.Column("cuit", sa.String(13), nullable=True),
        sa.Column("periodo", sa.String(7), nullable=True),
        sa.Column("fecha_vencimiento", sa.Date, nullable=True),
        sa.Column("monto", sa.Numeric(15, 2), nullable=True),
        sa.Column("codigo_impuesto", sa.String(50), nullable=True),
        sa.Column("concepto", sa.Text, nullable=True),
        sa.Column("codigo_cuenta", sa.String(20), nullable=True),
        sa.Column("nombre_cuenta", sa.String(200), nullable=True),
        sa.Column("regla_asignacion", sa.String(100), nullable=True),
        sa.Column("confianza_asignacion", sa.Numeric(3, 2), nullable=True),
        sa.Column("id_factura_doli", sa.Integer, nullable=True),
        sa.Column("id_pago_doli", sa.Integer, nullable=True),
        sa.Column("url_objeto_doli", sa.Text, nullable=True),
        sa.Column("datos_ocr_raw", postgresql.JSONB, nullable=True),
        sa.Column("log_procesamiento", postgresql.JSONB, server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("detalle_error", sa.Text, nullable=True),
        sa.Column("revisado_por", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("revisado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("eliminado_en", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_documentos_org_estado", "documentos_impositivos", ["org_id", "estado"])
    op.create_index("ix_documentos_cuit_periodo", "documentos_impositivos", ["cuit", "periodo"])

    # 6) Tabla movimientos_bancarios
    op.create_table(
        "movimientos_bancarios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cuenta_bancaria", sa.String(50), nullable=False),
        sa.Column("fecha_movimiento", sa.Date, nullable=False),
        sa.Column("fecha_valor", sa.Date, nullable=True),
        sa.Column("monto", sa.Numeric(15, 2), nullable=False),
        sa.Column("descripcion", sa.Text, nullable=True),
        sa.Column("referencia", sa.String(200), nullable=True),
        sa.Column("tipo_movimiento", sa.String(10), nullable=True),
        sa.Column("datos_raw", postgresql.JSONB, nullable=True),
        sa.Column("conciliado", sa.Boolean, server_default=sa.text("FALSE"), nullable=False),
        sa.Column("conciliado_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("documento_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("documentos_impositivos.id"), nullable=True),
        sa.Column(
            "confianza_match",
            postgresql.ENUM("HIGH", "MEDIUM", "LOW", "MANUAL", name="confianza_match", create_type=False),
            nullable=True,
        ),
        sa.Column("score_match", sa.Numeric(5, 4), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_movim_fecha_org", "movimientos_bancarios", ["fecha_movimiento", "org_id"])
    op.create_index("ix_movim_org_conciliado", "movimientos_bancarios", ["org_id", "conciliado"])

    # 7) Tabla reglas_contables
    op.create_table(
        "reglas_contables",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(200), nullable=False),
        sa.Column(
            "tipo_doc",
            postgresql.ENUM(
                "VEP", "DECLARACION_IVA", "DECLARACION_GANANCIAS", "SUSS", "IIBB", "FACTURA_PROVEEDOR", "OTRO",
                name="tipo_documento", create_type=False,
            ),
            nullable=True,
        ),
        sa.Column("patron_match", postgresql.JSONB, nullable=False),
        sa.Column("codigo_cuenta", sa.String(20), nullable=False),
        sa.Column("nombre_cuenta", sa.String(200), nullable=False),
        sa.Column("prioridad", sa.Integer, server_default="100", nullable=False),
        sa.Column("activa", sa.Boolean, server_default=sa.text("TRUE"), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    # 8) Tabla log_auditoria (solo escritura)
    op.create_table(
        "log_auditoria",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo_entidad", sa.String(50), nullable=False),
        sa.Column("id_entidad", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("accion", sa.String(50), nullable=False),
        sa.Column("estado_anterior", postgresql.JSONB, nullable=True),
        sa.Column("estado_nuevo", postgresql.JSONB, nullable=True),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("tipo_actor", sa.String(20), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_audit_entidad", "log_auditoria", ["tipo_entidad", "id_entidad"])


def downgrade() -> None:
    # Eliminar en orden inverso
    op.drop_index("ix_audit_entidad", table_name="log_auditoria")
    op.drop_table("log_auditoria")

    op.drop_table("reglas_contables")

    op.drop_index("ix_movim_org_conciliado", table_name="movimientos_bancarios")
    op.drop_index("ix_movim_fecha_org", table_name="movimientos_bancarios")
    op.drop_table("movimientos_bancarios")

    op.drop_index("ix_documentos_cuit_periodo", table_name="documentos_impositivos")
    op.drop_index("ix_documentos_org_estado", table_name="documentos_impositivos")
    op.drop_table("documentos_impositivos")

    op.drop_table("usuarios")
    op.drop_table("organizaciones")

    op.execute("DROP TYPE IF EXISTS rol_usuario;")
    op.execute("DROP TYPE IF EXISTS confianza_match;")
    op.execute("DROP TYPE IF EXISTS estado_documento;")
    op.execute("DROP TYPE IF EXISTS tipo_documento;")
