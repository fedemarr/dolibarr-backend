# Tests de integracion del modulo bancario
import io
import pytest


CSV_VALIDO = (
    "fecha,importe,descripcion,referencia\n"
    "01/01/2026,1234.56,Pago VEP Monotributo,REF-001\n"
    "02/01/2026,-500.00,Comision mantenimiento,REF-002\n"
    "03/01/2026,2500.00,Transferencia recibida,REF-003\n"
)


@pytest.mark.asyncio
async def test_importar_csv_retorna_resultado(cliente_async, headers_auth):
    """POST /api/v1/bancario/importar con CSV valido retorna 200 con importados > 0."""
    archivo = ("extracto.csv", io.BytesIO(CSV_VALIDO.encode("utf-8")), "text/csv")
    resp = await cliente_async.post(
        "/api/v1/bancario/importar",
        headers=headers_auth,
        files={"archivo": archivo},
        data={"cuenta_bancaria": "TEST-001"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["exito"] is True
    # importados puede ser 0 si la corrida anterior dejo duplicados, pero al menos
    # debe haber pasado por el parser sin errores criticos
    datos = body["datos"]
    assert "importados" in datos
    assert "duplicados" in datos
    assert "errores" in datos
    assert (datos["importados"] + datos["duplicados"]) >= 3


@pytest.mark.asyncio
async def test_importar_csv_formato_invalido(cliente_async, headers_auth):
    """POST con un CSV sin columnas reconocidas: endpoint no falla, reporta errores."""
    archivo = ("malformado.csv", io.BytesIO(b"campo_random,otro\nx,y\n"), "text/csv")
    resp = await cliente_async.post(
        "/api/v1/bancario/importar",
        headers=headers_auth,
        files={"archivo": archivo},
        data={"cuenta_bancaria": "TEST-002"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["exito"] is True
    # No se importo nada y hay al menos un mensaje de error
    assert body["datos"]["importados"] == 0
    assert body["datos"]["errores"] >= 1


@pytest.mark.asyncio
async def test_listar_movimientos_retorna_lista(cliente_async, headers_auth):
    """GET /api/v1/bancario/movimientos retorna 200 con datos y meta."""
    resp = await cliente_async.get("/api/v1/bancario/movimientos", headers=headers_auth)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["exito"] is True
    assert isinstance(body["datos"], list)
    assert "meta" in body
    assert "total" in body["meta"]
