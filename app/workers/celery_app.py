# Configuracion principal de Celery
from celery import Celery
from app.core.config import config


app_celery = Celery(
    "automatizacion_dolibarr",
    broker=config.REDIS_URL_EFECTIVA,
    backend=config.REDIS_URL_EFECTIVA,
    include=[
        "app.workers.pdf_tasks",
        "app.workers.bank_tasks",
        "app.workers.reconcile_tasks",
    ],
)

# Tarea programada: conciliacion automatica cada 6 horas
app_celery.conf.beat_schedule = {
    "conciliar-cada-6-horas": {
        "task": "app.workers.reconcile_tasks.conciliar_todas_las_orgs",
        "schedule": 21600,
    },
}
app_celery.conf.timezone = "America/Argentina/Buenos_Aires"
