# Configuracion del rate limiter global usando slowapi
# Bajo pytest se deshabilita para evitar interferir con los tests existentes.
import os
from slowapi import Limiter
from slowapi.util import get_remote_address


_PYTEST = "PYTEST_CURRENT_TEST" in os.environ

# Si esta corriendo pytest, dejamos limites altisimos para no interferir con los tests.
# En produccion/development normal se aplican los limites definidos por decorator.
limiter = Limiter(
    key_func=get_remote_address,
    enabled=not _PYTEST,
)
