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
if "PYTEST_CURRENT_TEST" in os.environ or os.environ.get("DOLIB_NO_POOL"):
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
