# Schemas Pydantic para el modulo de documentos
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import date, datetime


class RespuestaDocumento(BaseModel):
    id: uuid.UUID
    org_id: uuid.UUID
    nombre_original: str
    tipo_doc: Optional[str]
    estado: str
    cuit: Optional[str]
    periodo: Optional[str]
    fecha_vencimiento: Optional[date]
    monto: Optional[float]
    codigo_impuesto: Optional[str]
    concepto: Optional[str]
    codigo_cuenta: Optional[str]
    nombre_cuenta: Optional[str]
    confianza_asignacion: Optional[float]
    id_factura_doli: Optional[int]
    detalle_error: Optional[str]
    creado_en: datetime
    actualizado_en: datetime

    class Config:
        from_attributes = True


class RespuestaDocumentoResumido(BaseModel):
    id: uuid.UUID
    nombre_original: str
    tipo_doc: Optional[str]
    estado: str
    monto: Optional[float]
    periodo: Optional[str]
    creado_en: datetime

    class Config:
        from_attributes = True


class FiltrosDocumento(BaseModel):
    estado: Optional[str] = None
    tipo_doc: Optional[str] = None
    periodo: Optional[str] = None
    cuit: Optional[str] = None
    pagina: int = 1
    limite: int = 20


class SolicitudAprobar(BaseModel):
    # Permite enviar correcciones manuales al aprobar
    cuit: Optional[str] = None
    periodo: Optional[str] = None
    monto: Optional[float] = None
    codigo_cuenta: Optional[str] = None
    concepto: Optional[str] = None
