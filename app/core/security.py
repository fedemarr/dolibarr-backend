# Manejo de contrasenias y tokens JWT
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.core.config import config
from app.core.exceptions import ErrorApp

contexto_bcrypt = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password_plano: str) -> str:
    """Convierte una contrasenia en texto plano a hash bcrypt"""
    return contexto_bcrypt.hash(password_plano)


def verificar_password(password_plano: str, hash: str) -> bool:
    """Verifica si una contrasenia coincide con su hash"""
    return contexto_bcrypt.verify(password_plano, hash)


def crear_access_token(user_id: str, org_id: str) -> str:
    """Crea un JWT de acceso con expiracion configurada"""
    expiracion = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "org": org_id, "exp": expiracion, "tipo": "acceso"},
        config.SECRET_KEY,
        algorithm="HS256",
    )


def crear_refresh_token(user_id: str) -> str:
    """Crea un JWT de refresh con expiracion configurada"""
    expiracion = datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(
        {"sub": user_id, "exp": expiracion, "tipo": "refresh"},
        config.SECRET_KEY,
        algorithm="HS256",
    )


def decodificar_token(token: str) -> dict:
    """Decodifica y valida un JWT. Lanza ErrorApp 401 si es invalido o expirado"""
    try:
        return jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise ErrorApp(status_code=401, code="TOKEN_INVALIDO", message="Token invalido o expirado")
