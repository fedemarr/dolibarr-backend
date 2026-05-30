# Schemas Pydantic para reglas contables
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime


class SolicitudCrearRegla(BaseModel):
    nombre: str
    tipo_doc: Optional[str] = None
    patron_match: dict = {}
    codigo_cuenta: str
    nombre_cuenta: str
    prioridad: int = 100


class SolicitudActualizarRegla(BaseModel):
    nombre: Optional[str] = None
    tipo_doc: Optional[str] = None
    patron_match: Optional[dict] = None
    codigo_cuenta: Optional[str] = None
    nombre_cuenta: Optional[str] = None
    prioridad: Optional[int] = None
    activa: Optional[bool] = None


class RespuestaRegla(BaseModel):
    id: uuid.UUID
    nombre: str
    tipo_doc: Optional[str] = None
    patron_match: dict
    codigo_cuenta: str
    nombre_cuenta: str
    prioridad: int
    activa: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class SolicitudReordenar(BaseModel):
    ids_en_orden: list[uuid.UUID]
