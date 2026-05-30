# Servicio de conciliacion bancaria
# Calcula scores entre movimientos bancarios y documentos sincronizados
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Optional


@dataclass
class ScoreMatch:
    score: float
    detalle: dict


def calcular_score(
    monto_documento: Optional[float],
    fecha_documento: Optional[date],
    cuit_documento: Optional[str],
    codigo_impuesto: Optional[str],
    monto_banco: float,
    fecha_banco: date,
    descripcion_banco: str,
) -> ScoreMatch:
    """
    Calcula un score 0.0-1.0 de match entre un movimiento bancario y un documento.
    Pesos:
      - Monto exacto (tolerancia 0.1%): 0.50
      - Fecha dentro de ventana +/- 1d/5d/15d: 0.25
      - Referencia/codigo impuesto en descripcion: 0.15
      - CUIT en descripcion: 0.10
    """
    detalle = {}
    score = 0.0

    # 1) Match de monto (peso 0.50)
    if monto_documento is not None:
        diferencia = abs(float(monto_documento) - float(monto_banco))
        tolerancia = abs(float(monto_documento)) * 0.001  # 0.1%
        if diferencia <= max(tolerancia, 0.01):
            score += 0.50
            detalle["monto"] = "exacto"
        else:
            detalle["monto"] = f"diferencia={diferencia:.2f}"

    # 2) Match de fecha (peso 0.25)
    if fecha_documento is not None:
        delta = abs((fecha_banco - fecha_documento).days)
        if delta <= 1:
            score += 0.25
            detalle["fecha"] = "1d"
        elif delta <= 5:
            score += 0.15
            detalle["fecha"] = "5d"
        elif delta <= 15:
            score += 0.08
            detalle["fecha"] = "15d"
        else:
            detalle["fecha"] = f"delta={delta}d"

    # 3) Referencia / codigo de impuesto en descripcion (peso 0.15)
    descripcion_upper = (descripcion_banco or "").upper()
    if codigo_impuesto and codigo_impuesto in descripcion_upper:
        score += 0.15
        detalle["codigo_impuesto"] = "matcheado"

    # 4) CUIT en descripcion (peso 0.10)
    if cuit_documento:
        cuit_solo_numeros = cuit_documento.replace("-", "")
        if cuit_documento in descripcion_upper or cuit_solo_numeros in descripcion_upper.replace("-", ""):
            score += 0.10
            detalle["cuit"] = "matcheado"

    return ScoreMatch(score=min(score, 1.0), detalle=detalle)


def clasificar_confianza(score: float) -> str:
    """Mapea un score numerico a las etiquetas HIGH/MEDIUM/LOW."""
    if score >= 0.85:
        return "HIGH"
    if score >= 0.65:
        return "MEDIUM"
    return "LOW"
