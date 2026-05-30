"""Seed inicial: organizacion demo, usuario admin y reglas contables por defecto.

Revision ID: 0002_seed_data
Revises: 0001_initial_schema
Create Date: 2026-05-27
"""
from typing import Sequence, Union

from alembic import op
import json


revision: str = "0002_seed_data"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# IDs fijos para datos demo (asi son referenciables desde tests)
ORG_DEMO_ID = "00000000-0000-0000-0000-000000000001"
USUARIO_ADMIN_ID = "00000000-0000-0000-0000-000000000002"


def upgrade() -> None:
    # Import diferido para no romper si passlib no esta disponible en otros contextos
    from app.core.security import hashear_password

    # 1) Insertar organizacion demo
    op.execute(
        f"""
        INSERT INTO organizaciones (id, nombre, cuit, zona_horaria)
        VALUES ('{ORG_DEMO_ID}', 'Agencia Demo SA', '30-71234567-8', 'America/Argentina/Buenos_Aires');
        """
    )

    # 2) Insertar usuario administrador
    hash_admin = hashear_password("Admin1234!").replace("'", "''")
    op.execute(
        f"""
        INSERT INTO usuarios (id, org_id, email, password_hash, nombre, rol, activo)
        VALUES ('{USUARIO_ADMIN_ID}', '{ORG_DEMO_ID}', 'admin@demo.com',
                '{hash_admin}', 'Administrador', 'ADMIN', TRUE);
        """
    )

    # 3) Insertar reglas contables por defecto
    reglas = [
        (10, "VEP", {"codigo_impuesto": "030"}, "2.01.001", "IVA a pagar", "VEP - IVA"),
        (20, "VEP", {"codigo_impuesto": "767"}, "2.01.003", "Impuesto a las Ganancias", "VEP - Ganancias"),
        (30, "SUSS", {}, "2.01.005", "Cargas Sociales", "SUSS - Cargas Sociales"),
        (40, "IIBB", {}, "2.01.007", "Ingresos Brutos a pagar", "IIBB - Ingresos Brutos"),
        (999, None, {}, "2.99.001", "Impuestos pendientes de clasificar", "Default - Sin clasificar"),
    ]
    for prioridad, tipo_doc, patron, cuenta, nombre_cuenta, nombre in reglas:
        patron_json = json.dumps(patron).replace("'", "''")
        nombre_esc = nombre.replace("'", "''")
        cuenta_esc = nombre_cuenta.replace("'", "''")
        tipo_val = f"'{tipo_doc}'::tipo_documento" if tipo_doc else "NULL"
        op.execute(
            f"""
            INSERT INTO reglas_contables (org_id, nombre, tipo_doc, patron_match, codigo_cuenta, nombre_cuenta, prioridad, activa)
            VALUES ('{ORG_DEMO_ID}', '{nombre_esc}', {tipo_val}, '{patron_json}'::jsonb,
                    '{cuenta}', '{cuenta_esc}', {prioridad}, TRUE);
            """
        )


def downgrade() -> None:
    # Borrar en orden inverso
    op.execute(f"DELETE FROM reglas_contables WHERE org_id = '{ORG_DEMO_ID}';")
    op.execute(f"DELETE FROM usuarios WHERE id = '{USUARIO_ADMIN_ID}';")
    op.execute(f"DELETE FROM organizaciones WHERE id = '{ORG_DEMO_ID}';")
