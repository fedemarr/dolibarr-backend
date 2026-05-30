# Parser generico de ultimo recurso. Confianza maxima: 0.5.
import re
from datetime import datetime, date
from typing import Optional

from app.modules.ocr.parsers.base import ParserBase, DocumentoParsado


class GenericParser(ParserBase):
    """Parser de ultimo recurso para documentos que no matchearon a otros tipos."""

    # Patrones laxos - buscan en cualquier posicion del texto
    PATRON_CUIT_LAXO = re.compile(r"(\d{2}-\d{8}-\d{1})")
    PATRON_FECHA_LAXA = re.compile(r"(\d{2}/\d{2}/\d{4})")
    PATRON_MONTO_LAXO = re.compile(r"\$\s*([\d.,]+)")

    def parsear(self, texto: str) -> DocumentoParsado:
        if texto is None:
            texto = ""

        cuit = self._extraer_primero(self.PATRON_CUIT_LAXO, texto)

        fecha = None
        m_fecha = self.PATRON_FECHA_LAXA.search(texto)
        if m_fecha:
            try:
                fecha = datetime.strptime(m_fecha.group(1), "%d/%m/%Y").date()
            except ValueError:
                fecha = None

        # Buscar el monto mas alto encontrado en el texto
        monto = None
        montos = self.PATRON_MONTO_LAXO.findall(texto)
        if montos:
            valores = []
            for m_str in montos:
                v = self._convertir_monto_argentino(m_str)
                if v is not None:
                    valores.append(v)
            if valores:
                monto = max(valores)

        campos_encontrados = sum(1 for v in (cuit, fecha, monto) if v is not None)
        # Confianza maxima 0.5 (segun spec)
        confianza = min(0.5, (campos_encontrados / 3.0) * 0.5)

        return DocumentoParsado(
            tipo_doc="OTRO",
            cuit=cuit,
            periodo=None,
            fecha_vencimiento=fecha,
            monto=monto,
            codigo_impuesto=None,
            concepto=None,
            confianza=confianza,
            campos_raw={"longitud_texto": len(texto)},
        )

    @staticmethod
    def _extraer_primero(patron: re.Pattern, texto: str) -> Optional[str]:
        m = patron.search(texto)
        return m.group(1) if m else None
