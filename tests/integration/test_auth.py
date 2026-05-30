# Tests de integracion del modulo de autenticacion
# Usan el cliente HTTP async (ASGITransport) que apunta a la app FastAPI real,
# con la base de datos PostgreSQL real (seed cargado en migration 0002).
import pytest


@pytest.mark.asyncio
async def test_login_credenciales_correctas(cliente_async):
    resp = await cliente_async.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.com", "password": "Admin1234!"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["exito"] is True
    assert "access_token" in body["datos"]
    assert "refresh_token" in body["datos"]
    assert body["datos"]["usuario"]["email"] == "admin@demo.com"


@pytest.mark.asyncio
async def test_login_password_incorrecto(cliente_async):
    resp = await cliente_async.post(
        "/api/v1/auth/login",
        json={"email": "admin@demo.com", "password": "passwordIncorrecto"},
    )
    assert resp.status_code == 401
    body = resp.json()
    assert body["exito"] is False
    assert body["error"]["codigo"] == "CREDENCIALES_INVALIDAS"


@pytest.mark.asyncio
async def test_yo_sin_token_retorna_401(cliente_async):
    resp = await cliente_async.get("/api/v1/auth/yo")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_yo_con_token_retorna_usuario(cliente_async, headers_auth):
    resp = await cliente_async.get("/api/v1/auth/yo", headers=headers_auth)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["exito"] is True
    assert body["datos"]["email"] == "admin@demo.com"
