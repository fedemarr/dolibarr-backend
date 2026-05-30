# Parser para Volantes Electronicos de Pago (VEP) de AFIP
import re
from datetime import datetime, date
from typing import Optional

from app.modules.ocr.parsers.base import ParserBase, DocumentoParsado


class AfipVepParser(ParserBase):
    """Parser de Volantes Electronicos de Pago de AFIP.
    Nunca lanza excepcion: si no encuentra un campo lo deja en None."""

    # Patrones regex case-insensitive
    PATRON_CUIT = re.compile(r"CUIT[:\s]+(\d{2}-\d{8}-\d{1})", re.IGNORECASE)
    PATRON_MONTO = re.compile(
        r"(?:IMPORTE|TOTAL|MONTO)[:\s]+\$?\s*([\d.,]+)",
        re.IGNORECASE,
    )
    PATRON_VENCIMIENTO = re.compile(r"VENCIMIENTO[:\s]+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
    PATRON_PERIODO = re.compile(r"PERIODO[:\s]+(\d{2}/\d{4})", re.IGNORECASE)
    PATRON_CODIGO_IMPUESTO = re.compile(r"CONCEPTO[:\s]+(\d{3,6})", re.IGNORECASE)

    def parsear(self, texto: str) -> DocumentoParsado:
        if texto is None:
            texto = ""

        cuit = self._extraer_cuit(texto)
        monto = self._extraer_monto(texto)
        vencimiento = self._extraer_vencimiento(texto)
        periodo = self._extraer_periodo(texto)
        codigo_impuesto = self._extraer_codigo_impuesto(texto)

        # Confianza = campos encontrados / 4 (los 4 principales: cuit, monto, vencimiento, periodo)
        campos_encontrados = sum(
            1 for v in (cuit, monto, vencimiento, periodo) if v is not None
        )
        confianza = campos_encontrados / 4.0

        return DocumentoParsado(
            tipo_doc="VEP",
            cuit=cuit,
            periodo=periodo,
            fecha_vencimiento=vencimiento,
            monto=monto,
            codigo_impuesto=codigo_impuesto,
            concepto=None,
            confianza=confianza,
            campos_raw={
                "longitud_texto": len(texto),
            },
        )

    def _extraer_cuit(self, texto: str) -> Optional[str]:
        m = self.PATRON_CUIT.search(texto)
        return m.group(1) if m else None

    def _extraer_monto(self, texto: str) -> Optional[float]:
        m = self.PATRON_MONTO.search(texto)
        if not m:
            return None
        return self._convertir_monto_argentino(m.group(1))

    def _extraer_vencimiento(self, texto: str) -> Optional[date]:
        m = self.PATRON_VENCIMIENTO.search(texto)
        if not m:
            return None
        try:
            return datetime.strptime(m.group(1), "%d/%m/%Y").date()
        except ValueError:
            return None

    def _extraer_periodo(self, texto: str) -> Optional[str]:
        m = self.PATRON_PERIODO.search(texto)
        if not m:
            return None
        # Convertir MM/YYYY a YYYY-MM
        try:
            mes, anio = m.group(1).split("/")
            return f"{anio}-{mes}"
        except (ValueError, IndexError):
            return None

    def _extraer_codigo_impuesto(self, texto: str) -> Optional[str]:
        m = self.PATRON_CODIGO_IMPUESTO.search(texto)
        return m.group(1) if m else None
