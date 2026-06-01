# Funciones de alto nivel para crear facturas de proveedor en Dolibarr
from typing import Optional
from app.modules.dolibarr.client import ClienteDolibarr


def construir_payload_factura_proveedor(
    ref: str,
    monto: float,
    fecha_factura: str,
    codigo_cuenta: str,
    concepto: str,
    cuit: Optional[str] = None,
) -> dict:
    """Arma el JSON requerido por la API de Dolibarr para crear una factura proveedor."""
    return {
        "ref": ref,
        "type": 0,  # 0 = factura estandar
        "socid": 1,  # Proveedor por defecto (en produccion buscar por CUIT)
        "date": fecha_factura,
        "lines": [
            {
                "desc": concepto or ref,
                "subprice": monto,
                "qty": 1,
                "tva_tx": 0,
                "fk_accounting_account": codigo_cuenta,
            }
        ],
        "note_private": f"CUIT proveedor: {cuit}" if cuit else "",
    }


async def crear_factura(cliente: ClienteDolibarr, payload: dict) -> dict:
    """Crea una factura proveedor llamando al cliente Dolibarr."""
    return await cliente.crear_factura_proveedor(payload)


async def obtener_facturas_pendientes(cliente: ClienteDolibarr, limite: int = 500) -> list[dict]:
    """
    Obtiene facturas a clientes con estado pendiente de pago desde Dolibarr.
    Status 1 = validada/no pagada en Dolibarr.
    """
    try:
        # status=1 = validated/unpaid en Dolibarr
        respuesta = await cliente._cliente.get(
            "/invoices",
            params={"status": "1", "limit": limite, "sortfield": "t.rowid", "sortorder": "DESC"}
        )
        if respuesta.status_code == 200:
            datos = respuesta.json()
            if isinstance(datos, list):
                return datos
        return []
    except Exception:
        return []


async def registrar_pago_factura(
    cliente: ClienteDolibarr,
    id_factura: int,
    monto: float,
    fecha: str,
    cuenta_bancaria: str = "",
    nota: str = "Pago automático detectado en extracto bancario",
) -> dict | None:
    """
    Registra un pago en una factura de Dolibarr.
    Retorna el resultado o None si falla.
    """
    try:
        payload = {
            "datepaye": fecha,
            "paymentid": 6,  # 6 = transferencia bancaria en Dolibarr
            "closepaidinvoices": "yes",
            "accountid": 1,  # cuenta bancaria principal
            "num_paiement": "",
            "comment": nota,
            "chqemetteur": "",
            "chqbank": cuenta_bancaria,
            "amounts": {str(id_factura): monto},
        }
        respuesta = await cliente._cliente.post("/payments", json=payload)
        if respuesta.status_code in (200, 201):
            return respuesta.json()
        return None
    except Exception:
        return None
