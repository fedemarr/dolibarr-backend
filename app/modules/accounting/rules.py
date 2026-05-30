# Motor de reglas contables - decide que cuenta usar para cada documento
from dataclasses import dataclass
from typing import Optional


@dataclass
class AsignacionContable:
    codigo_cuenta: str
    nombre_cuenta: str
    nombre_regla: str
    confianza: float


class MotorReglasContables:
    """
    Asigna una cuenta contable a un documento basandose en reglas configurables.
    Las reglas se cargan desde la base de datos (no estan hardcodeadas).
    Se evaluan en orden de prioridad (menor numero = mayor prioridad).
    Si ninguna regla aplica, se usa la cuenta 2.99.001 (pendiente de clasificar).
    """

    async def asignar(
        self,
        tipo_doc: str,
        codigo_impuesto: Optional[str],
        monto: Optional[float],
        cuit: Optional[str],
        org_id: str,
        db,
    ) -> AsignacionContable:
        from sqlalchemy import select
        from app.modules.accounting.models import ReglaContable

        # Cargar reglas activas de la DB para esta organizacion, ordenadas por prioridad ASC
        resultado = await db.execute(
            select(ReglaContable)
            .where(ReglaContable.org_id == org_id, ReglaContable.activa == True)  # noqa: E712
            .order_by(ReglaContable.prioridad.asc())
        )
        reglas = resultado.scalars().all()

        for regla in reglas:
            if self._evaluar_patron(
                regla.patron_match, tipo_doc, codigo_impuesto, monto, cuit, regla.tipo_doc
            ):
                return AsignacionContable(
                    codigo_cuenta=regla.codigo_cuenta,
                    nombre_cuenta=regla.nombre_cuenta,
                    nombre_regla=regla.nombre,
                    confianza=0.9,
                )

        # Ninguna regla matcheo - usar cuenta de pendientes
        return AsignacionContable(
            codigo_cuenta="2.99.001",
            nombre_cuenta="Impuestos pendientes de clasificar",
            nombre_regla="Regla por defecto",
            confianza=0.0,
        )

    def _evaluar_patron(
        self,
        patron: dict,
        tipo_doc: str,
        codigo_impuesto: Optional[str],
        monto: Optional[float],
        cuit: Optional[str],
        tipo_doc_regla,
    ) -> bool:
        # Evalua si el patron JSONB coincide con los datos del documento.
        # tipo_doc_regla puede ser str (cuando viene del ENUM SQLAlchemy) o None.
        if tipo_doc_regla is not None:
            # Normalizar a string para comparar
            tipo_str = tipo_doc_regla.value if hasattr(tipo_doc_regla, "value") else str(tipo_doc_regla)
            if tipo_str != tipo_doc:
                return False
        if "codigo_impuesto" in patron and patron["codigo_impuesto"] != codigo_impuesto:
            return False
        if "cuit" in patron and patron["cuit"] != cuit:
            return False
        if "monto_min" in patron and monto is not None and monto < patron["monto_min"]:
            return False
        if "monto_max" in patron and monto is not None and monto > patron["monto_max"]:
            return False
        return True
