# Configuracion de Alembic para correr migrations contra PostgreSQL
import sys
from pathlib import Path
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# Agregar la raiz del proyecto al path para poder importar `app`
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from app.core.config import config as cfg_app
from app.core.database import Base

# Importar todos los modelos ORM para que Alembic los descubra automaticamente
from app.modules.auth import models as _auth_models  # noqa: F401
from app.modules.documents import models as _docs_models  # noqa: F401
from app.modules.accounting import models as _acct_models  # noqa: F401

# Objeto de configuracion de Alembic
config = context.config

# Inyectar la URL sincronica desde la configuracion de la app (Alembic usa psycopg2)
config.set_main_option("sqlalchemy.url", cfg_app.DATABASE_URL_SYNC)

# Configuracion de logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Corre migrations en modo offline (solo genera el SQL)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Corre migrations en modo online (conectado a la DB real)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
