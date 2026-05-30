# Parser para declaraciones juradas de IVA (Formulario 2002)
import re
from datetime import datetime, date
from typing import Optional

from app.modules.ocr.parsers.base import ParserBase, DocumentoParsado


class AfipIvaParser(ParserBase):
    """Parser de declaraciones juradas de IVA (F. 2002)."""

    PATRON_CUIT = re.compile(r"CUIT[:\s]+(\d{2}-\d{8}-\d{1})", re.IGNORECASE)
    PATRON_MONTO = re.compile(
        r"(?:IMPORTE|TOTAL|MONTO|SALDO\s+A\s+PAGAR)[:\s]+\$?\s*([\d.,]+)",
        re.IGNORECASE,
    )
    PATRON_VENCIMIENTO = re.compile(r"VENCIMIENTO[:\s]+(\d{2}/\d{2}/\d{4})", re.IGNORECASE)
    PATRON_PERIODO = re.compile(r"PERIODO[:\s]+(\d{2}/\d{4})", re.IGNORECASE)
    PATRON_DJ_IVA = re.compile(
        r"(DECLARACION\s+JURADA|F\.\s*2002|FORMULARIO\s+2002|\bDJ\b)",
        re.IGNORECASE,
    )

    def parsear(self, texto: str) -> DocumentoParsado:
        if texto is None:
            texto = ""

        # Verificar si parece DJ IVA - bono de confianza
        es_dj = bool(self.PATRON_DJ_IVA.search(texto))

        cuit = self._buscar(self.PATRON_CUIT, texto)
        monto = self._extraer_monto(texto)
        vencimiento = self._extraer_fecha(self.PATRON_VENCIMIENTO, texto)
        periodo = self._extraer_periodo(texto)

        campos_encontrados = sum(
            1 for v in (cuit, monto, vencimiento, periodo) if v is not None
        )
        confianza = campos_encontrados / 4.0
        if es_dj:
            confianza = min(1.0, confianza + 0.1)

        return DocumentoParsado(
            tipo_doc="DECLARACION_IVA",
            cuit=cuit,
            periodo=periodo,
            fecha_vencimiento=vencimiento,
            monto=monto,
            codigo_impuesto=None,
            concepto="Declaracion Jurada IVA" if es_dj else None,
            confianza=confianza,
            campos_raw={"es_dj": es_dj, "longitud_texto": len(texto)},
        )

    def _buscar(self, patron: re.Pattern, texto: str) -> Optional[str]:
        m = patron.search(texto)
        return m.group(1) if m else None

    def _extraer_monto(self, texto: str) -> Optional[float]:
        m = self.PATRON_MONTO.search(texto)
        if not m:
            return None
        return self._convertir_monto_argentino(m.group(1))

    def _extraer_fecha(self, patron: re.Pattern, texto: str) -> Optional[date]:
        m = patron.search(texto)
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
        try:
            mes, anio = m.group(1).split("/")
            return f"{anio}-{mes}"
        except (ValueError, IndexError):
            return None
