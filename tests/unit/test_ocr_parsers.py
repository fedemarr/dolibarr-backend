# Tests unitarios de los parsers de OCR
from datetime import date

from app.modules.ocr.parsers.afip_vep import AfipVepParser
from app.modules.ocr.parsers.afip_iva import AfipIvaParser
from app.modules.ocr.parsers.generic import GenericParser


TEXTO_VEP = """
VOLANTE ELECTRONICO DE PAGO
CUIT: 30-71234567-8
PERIODO: 04/2026
VENCIMIENTO: 28/05/2026
CONCEPTO: 030
IMPORTE: $124.500,00
"""


def test_parser_vep_extrae_todos_los_campos():
    parser = AfipVepParser()
    resultado = parser.parsear(TEXTO_VEP)

    assert resultado.cuit == "30-71234567-8"
    assert resultado.monto == 124500.0
    assert resultado.periodo == "2026-04"
    assert resultado.fecha_vencimiento == date(2026, 5, 28)
    assert resultado.codigo_impuesto == "030"
    assert resultado.confianza >= 0.9


def test_parser_vep_texto_vacio_no_lanza_excepcion():
    parser = AfipVepParser()
    resultado = parser.parsear("")
    assert resultado.cuit is None
    assert resultado.monto is None
    assert resultado.confianza == 0.0


def test_parser_iva_detecta_declaracion_jurada():
    parser = AfipIvaParser()
    texto = """
    DECLARACION JURADA F. 2002
    CUIT: 30-71234567-8
    PERIODO: 03/2026
    SALDO A PAGAR: $50.000,00
    VENCIMIENTO: 20/04/2026
    """
    resultado = parser.parsear(texto)
    assert resultado.tipo_doc == "DECLARACION_IVA"
    assert resultado.cuit == "30-71234567-8"
    assert resultado.monto == 50000.0
    assert resultado.confianza > 0.5


def test_parser_generico_confianza_maxima_05():
    parser = GenericParser()
    resultado = parser.parsear("Fecha 01/01/2026 monto $100,00 CUIT 30-12345678-9")
    assert resultado.confianza <= 0.5
    assert resultado.cuit == "30-12345678-9"
