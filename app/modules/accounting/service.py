# Servicio de procesamiento contable - une OCR + clasificacion + reglas contables
from pathlib import Path
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.ocr.engine import MotorOCR
from app.modules.classifier.rules_engine import ClasificadorDocumentos
from app.modules.accounting.rules import MotorReglasContables, AsignacionContable
from app.modules.ocr.parsers.afip_vep import AfipVepParser
from app.modules.ocr.parsers.afip_iva import AfipIvaParser
from app.modules.ocr.parsers.generic import GenericParser
from app.modules.ocr.parsers.base import DocumentoParsado


# Mapeo de tipo de documento -> instancia de parser
_PARSERS = {
    "VEP": AfipVepParser(),
    "DECLARACION_IVA": AfipIvaParser(),
}
_PARSER_GENERICO = GenericParser()


def seleccionar_parser(tipo_doc: str):
    """Devuelve el parser apropiado segun el tipo de documento."""
    return _PARSERS.get(tipo_doc, _PARSER_GENERICO)


async def procesar_documento(
    ruta_pdf: Path,
    org_id: str,
    db: AsyncSession,
) -> dict:
    """
    Pipeline completo: OCR -> clasificacion -> parsing -> asignacion contable.
    Retorna un dict con todos los campos extraidos y la asignacion contable.
    """
    motor_ocr = MotorOCR()
    clasificador = ClasificadorDocumentos()
    motor_reglas = MotorReglasContables()

    # 1) Extraer texto del PDF
    resultado_ocr = await motor_ocr.extraer(ruta_pdf)
    texto = resultado_ocr["texto"]

    # 2) Clasificar tipo de documento
    tipo_doc, confianza_clasif = clasificador.clasificar(texto)

    # 3) Parsear con el parser correspondiente
    parser = seleccionar_parser(tipo_doc)
    parsed: DocumentoParsado = parser.parsear(texto)

    # 4) Asignar cuenta contable
    asignacion: AsignacionContable = await motor_reglas.asignar(
        tipo_doc=tipo_doc,
        codigo_impuesto=parsed.codigo_impuesto,
        monto=parsed.monto,
        cuit=parsed.cuit,
        org_id=org_id,
        db=db,
    )

    # Confianza combinada (parsing + clasificacion + asignacion)
    confianza_global = min(parsed.confianza, confianza_clasif, asignacion.confianza or 0.5)

    return {
        "tipo_doc": tipo_doc,
        "cuit": parsed.cuit,
        "periodo": parsed.periodo,
        "fecha_vencimiento": parsed.fecha_vencimiento,
        "monto": parsed.monto,
        "codigo_impuesto": parsed.codigo_impuesto,
        "concepto": parsed.concepto,
        "codigo_cuenta": asignacion.codigo_cuenta,
        "nombre_cuenta": asignacion.nombre_cuenta,
        "regla_asignacion": asignacion.nombre_regla,
        "confianza_asignacion": confianza_global,
        "datos_ocr_raw": {
            "metodo_ocr": resultado_ocr["metodo"],
            "paginas": resultado_ocr["paginas"],
            "longitud_texto": len(texto),
            "confianza_clasificacion": confianza_clasif,
            "confianza_parsing": parsed.confianza,
            "campos_raw": parsed.campos_raw,
        },
    }
