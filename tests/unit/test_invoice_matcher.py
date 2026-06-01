# Tests del motor de matching entre movimientos bancarios y facturas
import pytest
from datetime import date
from app.modules.dolibarr.invoice_matcher import (
    calcular_score_factura,
    clasificar_confianza_factura,
    normalizar_texto,
)


def test_monto_exacto_da_score_alto():
    score, desglose = calcular_score_factura(
        monto_banco=100000.0,
        descripcion_banco="TRANSFERENCIA AFTICA S.A.",
        fecha_banco=date(2026, 5, 28),
        monto_factura=100000.0,
        nombre_tercero="Aftyka Sachon Industrias",
        fecha_factura=date(2026, 5, 27),
    )
    assert desglose["monto"] == 0.60
    assert score >= 0.60


def test_nombre_coincide_en_descripcion():
    score, desglose = calcular_score_factura(
        monto_banco=50000.0,
        descripcion_banco="COBRO FACTURA ECOFACTORY SRL",
        fecha_banco=date(2026, 5, 15),
        monto_factura=50000.0,
        nombre_tercero="ECOFACTORY S.R.L.",
        fecha_factura=date(2026, 5, 15),
    )
    assert desglose["nombre"] > 0
    assert score >= 0.85


def test_monto_diferente_score_bajo():
    score, desglose = calcular_score_factura(
        monto_banco=99000.0,
        descripcion_banco="PAGO CLIENTE",
        fecha_banco=date(2026, 5, 1),
        monto_factura=100000.0,
        nombre_tercero="CM ARG SRL",
        fecha_factura=date(2026, 5, 1),
    )
    assert desglose["monto"] < 0.60


def test_clasificar_confianza():
    assert clasificar_confianza_factura(0.90) == "HIGH"
    assert clasificar_confianza_factura(0.70) == "MEDIUM"
    assert clasificar_confianza_factura(0.40) == "LOW"


def test_normalizar_texto_quita_acentos():
    assert normalizar_texto("Aftyka Sachón") == "aftyka sachon"
    assert normalizar_texto("ECOFACTORY S.R.L.") == "ecofactory s r l"
