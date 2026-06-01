# Motor de matching entre movimientos bancarios y facturas pendientes en Dolibarr
# Cuando entra un pago al banco, busca la factura correspondiente en Dolibarr
# y la marca como pagada automáticamente

from dataclasses import dataclass
from decimal import Decimal
from datetime import date
from typing import Optional
import unicodedata
import re


@dataclass
class ResultadoMatch:
    factura_id: int
    factura_ref: str
    tercero: str
    monto_factura: float
    score: float
    confianza: str  # HIGH, MEDIUM, LOW
    desglose: dict


def normalizar_texto(texto: str) -> str:
    """Normaliza texto para comparación: minúsculas, sin acentos, sin caracteres especiales"""
    texto = texto.lower().strip()
    # Quitar acentos
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    # Solo letras y números
    texto = re.sub(r'[^a-z0-9\s]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def calcular_score_factura(
    monto_banco: float,
    descripcion_banco: str,
    fecha_banco: date,
    monto_factura: float,
    nombre_tercero: str,
    fecha_factura: date,
) -> tuple[float, dict]:
    """
    Calcula el score de match entre un movimiento bancario y una factura.

    Pesos:
    - Monto exacto (tolerancia 1%): 0.60
    - Nombre del tercero en descripción: 0.30
    - Fecha dentro de ventana razonable: 0.10
    """
    desglose = {"monto": 0.0, "nombre": 0.0, "fecha": 0.0}

    # Score por monto (60%)
    if monto_factura and monto_factura > 0:
        diferencia_pct = abs(monto_banco - monto_factura) / monto_factura
        if diferencia_pct <= 0.001:  # exacto o casi exacto
            desglose["monto"] = 0.60
        elif diferencia_pct <= 0.01:  # dentro del 1%
            desglose["monto"] = 0.45
        elif diferencia_pct <= 0.05:  # dentro del 5%
            desglose["monto"] = 0.20

    # Score por nombre del tercero (30%)
    if nombre_tercero:
        nombre_norm = normalizar_texto(nombre_tercero)
        desc_norm = normalizar_texto(descripcion_banco)
        palabras_nombre = [p for p in nombre_norm.split() if len(p) > 3]
        if palabras_nombre:
            matches = sum(1 for p in palabras_nombre if p in desc_norm)
            ratio = matches / len(palabras_nombre)
            desglose["nombre"] = round(ratio * 0.30, 3)

    # Score por fecha (10%)
    if fecha_factura and fecha_banco:
        from datetime import timedelta
        diff = abs((fecha_banco - fecha_factura).days)
        if diff <= 3:
            desglose["fecha"] = 0.10
        elif diff <= 15:
            desglose["fecha"] = 0.07
        elif diff <= 30:
            desglose["fecha"] = 0.04
        elif diff <= 60:
            desglose["fecha"] = 0.02

    score_total = sum(desglose.values())
    return round(score_total, 4), desglose


def clasificar_confianza_factura(score: float) -> str:
    if score >= 0.80:
        return "HIGH"
    elif score >= 0.60:
        return "MEDIUM"
    return "LOW"
