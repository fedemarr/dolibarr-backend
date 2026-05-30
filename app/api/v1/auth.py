# Endpoints de autenticacion: login, refresh y yo (usuario actual)
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.security import (
    crear_access_token,
    crear_refresh_token,
    decodificar_token,
)
from app.core.exceptions import ErrorApp
from app.core.limiter import limiter
from app.modules.auth.schemas import SolicitudLogin, RespuestaToken, SolicitudRefresh
from app.modules.auth.service import autenticar_usuario, obtener_usuario_actual
from app.modules.auth.models import Usuario


router = APIRouter(prefix="/api/v1/auth")


def _serializar_usuario(usuario: Usuario) -> dict:
    """Convierte un objeto Usuario en dict serializable JSON."""
    return {
        "id": str(usuario.id),
        "email": usuario.email,
        "nombre": usuario.nombre,
        "rol": usuario.rol,
        "org_id": str(usuario.org_id),
    }


@router.post("/login", response_model=None)
@limiter.limit("10/minute")
async def login(request: Request, datos: SolicitudLogin, db: AsyncSession = Depends(get_db)):
    """Autentica al usuario y retorna tokens JWT (access + refresh)."""
    usuario = await autenticar_usuario(datos.email, datos.password, db)

    access = crear_access_token(str(usuario.id), str(usuario.org_id))
    refresh = crear_refresh_token(str(usuario.id))

    return {
        "exito": True,
        "datos": {
            "access_token": access,
            "refresh_token": refresh,
            "tipo": "bearer",
            "usuario": _serializar_usuario(usuario),
        },
    }


@router.post("/refresh")
async def refresh(datos: SolicitudRefresh, db: AsyncSession = Depends(get_db)):
    """Recibe un refresh token valido y emite nuevos access+refresh tokens."""
    payload = decodificar_token(datos.refresh_token)
    if payload.get("tipo") != "refresh":
        raise ErrorApp(
            status_code=401,
            code="TOKEN_INVALIDO",
            message="Se requiere un token de refresh",
        )

    user_id_str = payload.get("sub")
    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise ErrorApp(status_code=401, code="TOKEN_INVALIDO", message="ID de usuario invalido en el token")

    resultado = await db.execute(
        select(Usuario).where(
            Usuario.id == user_id,
            Usuario.activo == True,  # noqa: E712
            Usuario.eliminado_en.is_(None),
        )
    )
    usuario = resultado.scalar_one_or_none()
    if usuario is None:
        raise ErrorApp(status_code=401, code="USUARIO_NO_ENCONTRADO", message="Usuario no encontrado")

    nuevo_access = crear_access_token(str(usuario.id), str(usuario.org_id))
    nuevo_refresh = crear_refresh_token(str(usuario.id))
    return {
        "exito": True,
        "datos": {
            "access_token": nuevo_access,
            "refresh_token": nuevo_refresh,
            "tipo": "bearer",
            "usuario": _serializar_usuario(usuario),
        },
    }


@router.get("/yo")
async def yo(usuario: Usuario = Depends(obtener_usuario_actual)):
    """Retorna los datos del usuario autenticado actual."""
    return {"exito": True, "datos": _serializar_usuario(usuario)}
