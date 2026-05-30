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
