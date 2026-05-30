# Cliente Redis compartido para tareas asincronas y rate-limiting
import redis.asyncio as aioredis
from app.core.config import config

# Cliente singleton de Redis. Se conecta lazy en el primer uso.
cliente_redis: aioredis.Redis = aioredis.from_url(
    config.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)


async def verificar_redis() -> bool:
    """Verifica que la conexion con Redis este viva"""
    try:
        return await cliente_redis.ping()
    except Exception:
        return False
