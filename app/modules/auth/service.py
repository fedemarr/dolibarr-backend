# Servicio de autenticacion: validar credenciales y obtener usuario actual desde JWT
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_db
from app.core.exceptions import ErrorApp
from app.core.security import verificar_password, decodificar_token
from app.modules.auth.models import Usuario


async def autenticar_usuario(email: str, password: str, db: AsyncSession) -> Usuario:
    """Busca un usuario activo por email y valida su contrasenia."""
    resultado = await db.execute(
        select(Usuario).where(
            Usuario.email == email,
            Usuario.activo == True,  # noqa: E712
            Usuario.eliminado_en.is_(None),
        )
    )
    usuario = resultado.scalar_one_or_none()
    if usuario is None or not verificar_password(password, usuario.password_hash):
        raise ErrorApp(
            status_code=401,
            code="CREDENCIALES_INVALIDAS",
            message="Email o contrasenia incorrectos",
        )
    return usuario


async def obtener_usuario_actual(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """Dependency FastAPI: decodifica el JWT del header Authorization y retorna el usuario."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise ErrorApp(
            status_code=401,
            code="TOKEN_FALTANTE",
            message="Falta el header Authorization con token Bearer",
        )

    token = authorization.split(" ", 1)[1].strip()
    payload = decodificar_token(token)

    if payload.get("tipo") != "acceso":
        raise ErrorApp(
            status_code=401,
            code="TOKEN_INVALIDO",
            message="Se requiere un token de acceso, no de refresh",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise ErrorApp(status_code=401, code="TOKEN_INVALIDO", message="Token sin sujeto")

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
        raise ErrorApp(status_code=401, code="USUARIO_NO_ENCONTRADO", message="Usuario no encontrado o inactivo")
    return usuario
