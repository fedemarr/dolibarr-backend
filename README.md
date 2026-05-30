# Automatizacion Dolibarr

Sistema de automatizacion de boletas AFIP y conciliacion bancaria para Dolibarr ERP.

## Arranque rapido

### Terminal 1 - API

```powershell
cd C:\Users\fede\Documents\automatizaciondolibar
.\venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --reload --port 8000
```

### Terminal 2 - Worker Celery

```powershell
cd C:\Users\fede\Documents\automatizaciondolibar
.\venv\Scripts\Activate.ps1
py -m celery -A app.workers.celery_app worker --loglevel=info --pool=solo
```

### Terminal 3 - Celery Beat (tareas programadas)

```powershell
cd C:\Users\fede\Documents\automatizaciondolibar
.\venv\Scripts\Activate.ps1
py -m celery -A app.workers.celery_app beat --loglevel=info
```

## URLs

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Credenciales de prueba

- Email: `admin@demo.com`
- Password: `Admin1234!`

## Conectar con Dolibarr real

1. En Dolibarr: Configuracion -> API -> Generar clave
2. En `.env`: `DOLIBARR_API_KEY=tu_clave_real` y `DOLIBARR_URL=http://tu-dolibarr`

## Importar extracto bancario

```bash
curl -X POST http://localhost:8000/api/v1/bancario/importar \
  -H "Authorization: Bearer TU_TOKEN" \
  -F "archivo=@extracto.csv" \
  -F "cuenta_bancaria=Galicia-001"
```

## Agregar regla contable

```bash
curl -X POST http://localhost:8000/api/v1/reglas \
  -H "Authorization: Bearer TU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Monotributo","tipo_doc":"VEP","patron_match":{"codigo_impuesto":"217"},"codigo_cuenta":"2.01.009","nombre_cuenta":"Monotributo a pagar","prioridad":25}'
```

## Notas importantes

- bcrypt fijado en 4.0.1 (incompatible con 5.x + passlib)
- Celery worker en Windows requiere `--pool=solo`
- PDFs se guardan en `C:\tmp\dolibarr_pdfs\` (S3 para produccion)
