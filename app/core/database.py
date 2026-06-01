# Motor de base de datos asincrono con SQLAlchemy
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import NullPool
from app.core.config import config

# Bajo pytest usamos NullPool para evitar problemas de event-loop entre tests en Windows + Py 3.14
_engine_kwargs = {
    "echo": False,  # silencioso en tests; en dev se controla por logger
}
# Usar NullPool en pytest, workers Celery y cuando se pida explicitamente.
# Los workers crean un event loop nuevo por tarea — el pool de asyncpg no puede
# reutilizarse entre loops distintos, causando fallas silenciosas.
_es_worker = os.environ.get("CELERY_WORKER_RUNNING") == "1"
_es_test = "PYTEST_CURRENT_TEST" in os.environ
_sin_pool = os.environ.get("DOLIB_NO_POOL") == "1"

if _es_worker or _es_test or _sin_pool:
    _engine_kwargs["poolclass"] = NullPool
else:
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["echo"] = config.ENVIRONMENT == "development"

engine = create_async_engine(config.DATABASE_URL, **_engine_kwargs)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_db():
    # Dependency de FastAPI - provee una sesion async por request
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
