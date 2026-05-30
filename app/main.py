# Punto de entrada de la aplicacion FastAPI
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import config
from app.core.database import get_db
from app.core.exceptions import ErrorApp, manejador_errores
from app.core.limiter import limiter
from app.api.v1 import auth, documents, banking, reconciliation, rules, reports


def crear_app() -> FastAPI:
    app = FastAPI(
        title="API de Automatizacion Dolibarr",
        description="Sistema de automatizacion de boletas AFIP y conciliacion bancaria",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Rate limiter (solo activo fuera de pytest)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # CORS — incluye URL del frontend de Vercel si esta configurada
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://localhost:3003",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ]
    frontend_url = os.getenv("FRONTEND_URL")
    if frontend_url:
        origins.append(frontend_url)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(ErrorApp, manejador_errores)

    app.include_router(auth.router, tags=["autenticacion"])
    app.include_router(documents.router, tags=["documentos"])
    app.include_router(banking.router, tags=["bancario"])
    app.include_router(reconciliation.router, tags=["conciliacion"])
    app.include_router(rules.router, tags=["reglas"])
    app.include_router(reports.router, tags=["reportes"])

    @app.get("/health", tags=["sistema"])
    async def verificar_estado():
        """Health check — siempre retorna 200 para que Railway no mate el proceso."""
        estado = {
            "estado": "ok",
            "version": "1.0.0",
            "ambiente": config.ENVIRONMENT,
            "servicios": {},
        }

        # Verificar base de datos (sin dependency injection para no fallar si DB no arranco)
        try:
            from app.core.database import SessionLocal
            from sqlalchemy import text
            async with SessionLocal() as db:
                await db.execute(text("SELECT 1"))
            estado["servicios"]["base_datos"] = "ok"
        except Exception as e:
            estado["servicios"]["base_datos"] = f"error: {str(e)[:100]}"
            estado["estado"] = "degradado"

        # Verificar Redis (leer directamente del entorno para evitar cache de Pydantic)
        try:
            import os
            import redis as redis_sync
            redis_url = os.getenv("REDIS_URL") or config.REDIS_URL
            estado["debug_redis_url"] = redis_url[:30] + "..."  # solo para debug
            r = redis_sync.from_url(redis_url, socket_connect_timeout=2)
            r.ping()
            estado["servicios"]["redis"] = "ok"
        except Exception as e:
            estado["servicios"]["redis"] = f"error: {str(e)[:100]}"
            estado["estado"] = "degradado"

        return estado

    # Schema OpenAPI con boton Authorize para JWT en Swagger
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title="API de Automatizacion Dolibarr",
            version="1.0.0",
            description="Sistema de automatizacion de boletas AFIP y conciliacion bancaria",
            routes=app.routes,
        )
        schema.setdefault("components", {})
        schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Pegar el access_token obtenido en /api/v1/auth/login",
            }
        }
        schema["security"] = [{"BearerAuth": []}]
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[method-assign]

    return app


app = crear_app()
