# Excepciones personalizadas del sistema y manejadores para FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse


class ErrorApp(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        self.status_code = status_code
        self.code = code
        self.message = message
        super().__init__(message)


async def manejador_errores(request: Request, exc: ErrorApp) -> JSONResponse:
    # Formato estandar de error para todas las respuestas de error de la API
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "exito": False,
            "error": {
                "codigo": exc.code,
                "mensaje": exc.message,
            },
        },
    )
