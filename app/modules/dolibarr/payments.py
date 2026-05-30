# Funciones de alto nivel para registrar pagos en Dolibarr
from app.modules.dolibarr.client import ClienteDolibarr


def construir_payload_pago(monto: float, fecha_pago: str, id_cuenta_bancaria: int, ref: str = "") -> dict:
    """Arma el JSON requerido por la API de Dolibarr para registrar un pago."""
    return {
        "datepaye": fecha_pago,
        "paymentid": 1,  # tipo de pago por defecto (transferencia)
        "closepaidinvoices": "yes",
        "accountid": id_cuenta_bancaria,
        "amounts": {"amount": monto},
        "num_payment": ref,
    }


async def registrar_pago(cliente: ClienteDolibarr, id_factura: int, payload: dict) -> dict:
    """Registra un pago contra una factura existente en Dolibarr."""
    return await cliente.crear_pago(id_factura, payload)
