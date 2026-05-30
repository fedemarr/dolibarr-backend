# Schemas Pydantic para autenticacion
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid


class SolicitudLogin(BaseModel):
    email: str
    password: str


class RespuestaToken(BaseModel):
    access_token: str
    refresh_token: str
    tipo: str = "bearer"
    usuario: dict


class SolicitudRefresh(BaseModel):
    refresh_token: str


class RespuestaUsuario(BaseModel):
    id: uuid.UUID
    email: str
    nombre: str
    rol: str
    org_id: uuid.UUID

    class Config:
        from_attributes = True
