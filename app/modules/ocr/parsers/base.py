# Clase base y dataclass de salida para todos los parsers de documentos
from dataclasses import dataclass, field
from typing import Optional
from datetime import date


@dataclass
class DocumentoParsado:
    tipo_doc: str
    cuit: Optional[str] = None
    periodo: Optional[str] = None        # formato YYYY-MM
    fecha_vencimiento: Optional[date] = None
    monto: Optional[float] = None
    codigo_impuesto: Optional[str] = None
    concepto: Optional[str] = None
    confianza: float = 0.0               # 0.0 a 1.0
    campos_raw: dict = field(default_factory=dict)


class ParserBase:
    """Clase base para todos los parsers de documentos.
    Las subclases deben implementar parsear()."""

    def parsear(self, texto: str) -> DocumentoParsado:
        raise NotImplementedError("Cada parser debe implementar parsear()")

    @staticmethod
    def _convertir_monto_argentino(monto_str: str) -> Optional[float]:
        """Convierte un string de monto en formato argentino ('1.234,56') a float."""
        if not monto_str:
            return None
        # Limpiar simbolos de moneda y espacios
        s = monto_str.strip().replace("$", "").replace(" ", "")
        try:
            # Formato argentino: punto=miles, coma=decimal
            if "," in s and "." in s:
                # Asumimos que la coma es el separador decimal
                s = s.replace(".", "").replace(",", ".")
            elif "," in s:
                s = s.replace(",", ".")
            return float(s)
        except (ValueError, AttributeError):
            return None
