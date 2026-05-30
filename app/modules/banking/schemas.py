# Schemas Pydantic para el modulo bancario
from pydantic import BaseModel
from decimal import Decimal
from datetime import date, datetime
from typing import Optional
import uuid


class RespuestaMovimiento(BaseModel):
    id: uuid.UUID
    cuenta_bancaria: str
    fecha_movimiento: date
    monto: Decimal
    descripcion: Optional[str] = None
    referencia: Optional[str] = None
    tipo_movimiento: Optional[str] = None
    conciliado: bool
    confianza_match: Optional[str] = None
    score_match: Optional[float] = None
    documento_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True


class FiltrosMovimiento(BaseModel):
    conciliado: Optional[bool] = None
    fecha_desde: Optional[date] = None
    fecha_hasta: Optional[date] = None
    cuenta: Optional[str] = None
    pagina: int = 1
    limite: int = 50


class SolicitudImportar(BaseModel):
    cuenta_bancaria: str
    formato: str  # "csv" o "ofx"


class RespuestaImportacion(BaseModel):
    importados: int
    duplicados: int
    errores: int
    detalle_errores: list[str] = []
