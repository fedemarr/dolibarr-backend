# Placeholder de tareas relacionadas a movimientos bancarios.
# Sera implementado en Sesion 2 (parseo de extractos CSV/OFX/XLS).
from app.workers.celery_app import app_celery


@app_celery.task(name="app.workers.bank_tasks.importar_movimientos_bancarios")
def importar_movimientos_bancarios(*args, **kwargs) -> dict:
    """Placeholder - importar extractos bancarios (CSV / OFX / XLS). Pendiente Sesion 2."""
    return {
        "estado": "pendiente_implementacion",
        "mensaje": "Importacion de movimientos bancarios sera implementada en Sesion 2",
    }
