# Cliente HTTP para la REST API de Dolibarr
# IMPORTANTE: nunca conectar directamente a la base de datos de Dolibarr
# Toda comunicacion es exclusivamente por REST API

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import config
from app.core.exceptions import ErrorApp


class DolibarrError(ErrorApp):
    def __init__(self, mensaje: str, status_code: int = 502):
        super().__init__(
            status_code=status_code,
            code="ERROR_DOLIBARR",
            message=f"Error al comunicarse con Dolibarr: {mensaje}",
        )


class ClienteDolibarr:
    """
    Wrapper sobre la REST API de Dolibarr.
    Reintentos automaticos con backoff exponencial (hasta 3 intentos).
    Todos los errores HTTP se convierten en DolibarrError tipado.
    Timeout de 30 segundos por request.
    """

    def __init__(self):
        self._cliente = httpx.AsyncClient(
            base_url=f"{config.DOLIBARR_URL}/api/index.php",
            headers={"DOLAPIKEY": config.DOLIBARR_API_KEY},
            timeout=30.0,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def crear_factura_proveedor(self, datos: dict) -> dict:
        """Crea una factura de proveedor en Dolibarr."""
        respuesta = await self._cliente.post("/invoices", json=datos)
        self._verificar_respuesta(respuesta)
        return respuesta.json()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
    async def crear_pago(self, id_factura: int, datos: dict) -> dict:
        """Registra un pago sobre una factura existente."""
        respuesta = await self._cliente.post(f"/invoices/{id_factura}/payments", json=datos)
        self._verificar_respuesta(respuesta)
        return respuesta.json()

    async def obtener_cuenta_contable(self, codigo: str) -> dict | None:
        """Busca una cuenta contable por codigo."""
        try:
            respuesta = await self._cliente.get(f"/accountancy/account/{codigo}")
            if respuesta.status_code == 404:
                return None
            self._verificar_respuesta(respuesta)
            return respuesta.json()
        except httpx.RequestError:
            return None

    async def verificar_conexion(self) -> bool:
        """Verifica que Dolibarr este accesible y la API key sea valida."""
        try:
            respuesta = await self._cliente.get("/status")
            return respuesta.status_code == 200
        except Exception:
            return False

    def _verificar_respuesta(self, respuesta: httpx.Response) -> None:
        # Convierte errores HTTP en DolibarrError con mensaje en espaniol
        if respuesta.status_code >= 400:
            raise DolibarrError(f"HTTP {respuesta.status_code}: {respuesta.text}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self._cliente.aclose()
