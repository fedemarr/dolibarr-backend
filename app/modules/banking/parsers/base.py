# Tipos base para parsers de extractos bancarios
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class MovimientoBancarioParsado:
    fecha: date
    fecha_valor: Optional[date]
    monto: Decimal              # positivo = credito, negativo = debito
    descripcion: str
    referencia: Optional[str]
    tipo: str                   # DEBITO o CREDITO
    datos_raw: dict = field(default_factory=dict)


class ParserBancarioBase:
    """Clase base para parsers de extractos bancarios"""

    def parsear(self, contenido: bytes) -> tuple[list[MovimientoBancarioParsado], list[str]]:
        """
        Parsea el extracto y retorna (movimientos, errores).
        Nunca lanza excepcion - filas invalidas se agregan a errores.
        """
        raise NotImplementedError
