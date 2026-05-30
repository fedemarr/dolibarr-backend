# Fixtures comunes para tests pytest
import sys
import uuid
from pathlib import Path
import pytest
import pytest_asyncio

# Agregar la raiz del proyecto al path para imports
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))


# UUIDs fijos correspondientes a los datos seed (definidos en migration 0002)
ORG_DEMO_ID = "00000000-0000-0000-0000-000000000001"
USUARIO_ADMIN_ID = "00000000-0000-0000-0000-000000000002"


@pytest_asyncio.fixture
async def cliente_async():
    """Cliente HTTP async usando ASGITransport (sin red real)."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as cli:
        yield cli


@pytest.fixture
def headers_auth():
    """Headers con un JWT valido del usuario admin (generado en proceso)."""
    from app.core.security import crear_access_token

    token = crear_access_token(USUARIO_ADMIN_ID, ORG_DEMO_ID)
    return {"Authorization": f"Bearer {token}"}
