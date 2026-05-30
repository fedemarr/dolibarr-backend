# Tests del scoring de conciliacion bancaria (placeholder - se expandira en Sesion 2)
from datetime import date
from app.modules.reconciliation.service import calcular_score, clasificar_confianza


def test_score_monto_exacto_y_fecha_misma_dia():
    sm = calcular_score(
        monto_documento=100.0,
        fecha_documento=date(2026, 5, 1),
        cuit_documento="30-12345678-9",
        codigo_impuesto="030",
        monto_banco=100.0,
        fecha_banco=date(2026, 5, 1),
        descripcion_banco="PAGO IMPUESTO 030 CUIT 30-12345678-9",
    )
    # Monto 0.50 + fecha 0.25 + codigo 0.15 + cuit 0.10 = 1.00
    assert sm.score >= 0.95


def test_clasificar_confianza_high_medium_low():
    assert clasificar_confianza(0.90) == "HIGH"
    assert clasificar_confianza(0.70) == "MEDIUM"
    assert clasificar_confianza(0.40) == "LOW"


def test_score_solo_monto_distinto_fecha_lejana():
    sm = calcular_score(
        monto_documento=100.0,
        fecha_documento=date(2026, 1, 1),
        cuit_documento=None,
        codigo_impuesto=None,
        monto_banco=200.0,
        fecha_banco=date(2026, 6, 1),
        descripcion_banco="otra cosa",
    )
    assert sm.score < 0.5
