# Progreso de Automatizacion Dolibarr

Implementacion iniciada el 2026-05-27.

## Resumen de pasos

- [PASO 1] OK Entorno virtual creado e instaladas todas las dependencias (fastapi, sqlalchemy, alembic, celery, pdfplumber, jose, passlib, boto3, structlog, pytest, psycopg2-binary, etc.)
- [PASO 2] OK Estructura de carpetas y archivos __init__.py creados
- [PASO 3] OK Archivo .env creado con variables de configuracion
- [PASO 4] OK app/core/config.py implementado con Pydantic Settings
- [PASO 5] OK app/core/database.py implementado con motor async SQLAlchemy + asyncpg (usa NullPool bajo pytest)
- [PASO 6] OK app/core/exceptions.py y app/core/redis.py implementados
- [PASO 7] OK app/core/security.py implementado (bcrypt + JWT access/refresh)
- [PASO 8] OK Alembic inicializado, migrations 0001_initial_schema y 0002_seed_data ejecutadas contra dolibarr_automation. Usuario admin@demo.com creado con password Admin1234! y 5 reglas contables. (Nota: se hizo downgrade de bcrypt a 4.0.1 por incompatibilidad con passlib 1.7.4 + bcrypt 5.x)
- [PASO 9] OK Modulo auth: models (Usuario, Organizacion), schemas Pydantic, service y endpoints /login /refresh /yo
- [PASO 10] OK Motor OCR (pdfplumber + easyocr lazy) y parsers (base, afip_vep, afip_iva, generic)
- [PASO 11] OK Clasificador de documentos por palabras clave
- [PASO 12] OK Motor de reglas contables (carga reglas de DB, evalua patrones JSONB) y servicio orquestador
- [PASO 13] OK Cliente Dolibarr (HTTP async + retry exponencial), invoices.py y payments.py
- [PASO 14] OK Maquina de estados (transiciones validas), events.py (auditoria) y service.py (scoring de conciliacion)
- [PASO 15] OK Modulo documentos: models, schemas, repository, service y endpoints REST (/subir /detalle /listar /aprobar /reintentar /preview)
- [PASO 16] OK Workers Celery: celery_app.py, pdf_tasks (procesar_pdf, sincronizar_con_dolibarr), bank_tasks (placeholder), reconcile_tasks (conciliacion automatica con scoring)
- [PASO 17] OK app/main.py implementado (FastAPI con CORS, manejador de errores, routers v1 y endpoint /health)
- [PASO 18] OK Tests: conftest, 4 tests de OCR parsers, 6 tests de state machine, 3 tests de bank matcher, 4 tests de integracion auth
- [PASO 19] OK Verificacion: 17/17 tests pasando, servidor uvicorn levanta correctamente, /health responde 200, login real con admin@demo.com retorna tokens
- [PASO 20] OK Documento PROGRESS.md actualizado con resumen final

## Endpoints implementados y funcionando

| Metodo | Ruta                                | Descripcion                              |
|--------|-------------------------------------|------------------------------------------|
| GET    | /health                             | Verificacion de estado del sistema       |
| GET    | /docs                               | Swagger UI                               |
| GET    | /redoc                              | ReDoc                                    |
| POST   | /api/v1/auth/login                  | Login con email + password               |
| POST   | /api/v1/auth/refresh                | Refrescar tokens                         |
| GET    | /api/v1/auth/yo                     | Datos del usuario autenticado            |
| POST   | /api/v1/documentos/subir            | Subir PDF (multipart/form-data)          |
| GET    | /api/v1/documentos                  | Listar paginado con filtros              |
| GET    | /api/v1/documentos/{id}             | Detalle completo de un documento         |
| PATCH  | /api/v1/documentos/{id}/aprobar     | Aprobar (con correcciones opcionales)    |
| PATCH  | /api/v1/documentos/{id}/reintentar  | Reintentar procesamiento si esta en ERROR|
| GET    | /api/v1/documentos/{id}/preview     | Descargar/visualizar el PDF original     |

## Tests

17/17 tests pasando:
- 4 tests integracion auth (test_auth.py)
- 6 tests maquina de estados (test_state_machine.py)
- 4 tests parsers OCR (test_ocr_parsers.py)
- 3 tests bank matcher (test_bank_matcher.py)

## Como iniciar el servidor

Desde PowerShell, parado en C:\Users\fede\Documents\automatizaciondolibar:

```powershell
# 1) Activar entorno virtual
& "C:\Users\fede\Documents\automatizaciondolibar\venv\Scripts\Activate.ps1"

# 2) (Opcional) Reaplicar migrations
py -m alembic upgrade head

# 3) Iniciar API
py -m uvicorn app.main:app --reload --port 8000

# 4) Iniciar worker Celery (en otra consola, requiere Redis corriendo)
py -m celery -A app.workers.celery_app:app_celery worker --loglevel=info --pool=solo

# 5) Iniciar Celery beat (programador de tareas periodicas, opcional)
py -m celery -A app.workers.celery_app:app_celery beat --loglevel=info
```

API disponible en http://localhost:8000  (Swagger en /docs)

## Credenciales de prueba

- Email: admin@demo.com
- Password: Admin1234!
- Rol: ADMIN
- Organizacion: Agencia Demo SA (CUIT 30-71234567-8)
- IDs fijos (utiles para tests):
  - org_id: 00000000-0000-0000-0000-000000000001
  - usuario_id: 00000000-0000-0000-0000-000000000002

## Conexion a la base de datos

- Host: localhost:5432
- Database: dolibarr_automation
- Usuario: automation_user / automation_pass_dev
- 5 reglas contables sembradas (VEP-IVA, VEP-Ganancias, SUSS, IIBB, default)

## Sesion 2 (iniciada 2026-05-29)

- [PASO 1] OK Modulo banking/parsers creado: base.py, csv_parser.py (formato argentino), ofx_parser.py (con fallback regex). Dependencia ofxparse 0.21 instalada.
- [PASO 2] OK Modulo banking: models.py (re-exporta MovimientoBancario), schemas.py, repository.py (con deduplicacion por referencia o fecha+monto+desc), service.py (importar_archivo).
- [PASO 3] OK Endpoints bancarios en app/api/v1/banking.py: POST /importar, GET /movimientos, GET /movimientos/{id}, POST /conciliar, PATCH /movimientos/{id}/match. Tambien agregada task Celery conciliar_org en reconcile_tasks.py.
- [PASO 4] OK Panel de conciliacion en app/api/v1/reconciliation.py: GET /pendientes (con sugerencias scoreadas), POST /confirmar, GET /historial. Reusa calcular_score y clasificar_confianza existentes. LogAuditoria ya existia en documents/models.py.
- [PASO 5] OK Endpoints de reglas contables en app/api/v1/rules.py: GET, POST, PUT/{id}, DELETE/{id}, POST /reordenar. Schemas en app/modules/accounting/schemas.py.
- [PASO 6] OK Endpoints de reportes en app/api/v1/reports.py: GET /resumen (por periodo), GET /vencimientos-proximos, GET /actividad.
- [PASO 7] OK Rate limiting con slowapi: app/core/limiter.py (deshabilitado bajo pytest), middleware en main.py, decoradores @limiter.limit en /login (10/min) y /subir (20/min).
- [PASO 8] OK Modulo notifications: channels/slack.py, channels/email.py (ambos best-effort, loguean si placeholder), service.py con ServicioNotificaciones. Integrado en pdf_tasks (revision + error_sync) y reconcile_tasks (conciliacion automatica).
- [PASO 9] OK Tests integracion: tests/integration/test_documentos.py (4 tests: listar, subir invalido, no encontrado, aislamiento multi-tenant), tests/integration/test_bancario.py (3 tests: importar csv valido, csv malformado, listar). 24/24 pasan.
- [PASO 10] OK Routers banking, reconciliation, rules y reports registrados en app/main.py (ya hecho en PASO 7). README.md creado en raiz.
- [PASO 11] OK Verificacion final: 24/24 tests pasan; uvicorn arranca y /health responde 200; 25 rutas API + 5 utilitarias registradas.

## Resumen final Sesion 2

### Tests
24/24 pasan (17 originales + 7 nuevos):
- 4 integracion auth
- 4 integracion documentos (listar, subir invalido, no encontrado, aislamiento multi-tenant)
- 3 integracion bancario (importar csv valido, csv malformado, listar)
- 3 unit bank_matcher
- 4 unit ocr_parsers
- 6 unit state_machine

### Endpoints totales (25 API)

| Metodo | Ruta                                       | Descripcion                              |
|--------|--------------------------------------------|------------------------------------------|
| GET    | /health                                    | Estado del sistema                       |
| POST   | /api/v1/auth/login                         | Login (rate-limited 10/min)              |
| POST   | /api/v1/auth/refresh                       | Refresh tokens                           |
| GET    | /api/v1/auth/yo                            | Usuario autenticado                      |
| POST   | /api/v1/documentos/subir                   | Subir PDF (rate-limited 20/min)          |
| GET    | /api/v1/documentos                         | Listar paginado                          |
| GET    | /api/v1/documentos/{id}                    | Detalle                                  |
| PATCH  | /api/v1/documentos/{id}/aprobar            | Aprobar y sincronizar                    |
| PATCH  | /api/v1/documentos/{id}/reintentar         | Reintento si ERROR                       |
| GET    | /api/v1/documentos/{id}/preview            | Descargar PDF                            |
| POST   | /api/v1/bancario/importar                  | Importar extracto CSV u OFX              |
| GET    | /api/v1/bancario/movimientos               | Listar movimientos paginado              |
| GET    | /api/v1/bancario/movimientos/{id}          | Detalle de movimiento                    |
| POST   | /api/v1/bancario/conciliar                 | Disparar conciliacion manual             |
| PATCH  | /api/v1/bancario/movimientos/{id}/match    | Match manual movimiento-documento        |
| GET    | /api/v1/conciliacion/pendientes            | Movimientos no conciliados + sugerencias |
| POST   | /api/v1/conciliacion/confirmar             | Confirmar match manual                   |
| GET    | /api/v1/conciliacion/historial             | Ultimas conciliaciones                   |
| GET    | /api/v1/reglas                             | Listar reglas contables                  |
| POST   | /api/v1/reglas                             | Crear regla                              |
| PUT    | /api/v1/reglas/{id}                        | Actualizar regla                         |
| DELETE | /api/v1/reglas/{id}                        | Desactivar regla                         |
| POST   | /api/v1/reglas/reordenar                   | Reordenar prioridades                    |
| GET    | /api/v1/reportes/resumen                   | Resumen por periodo                      |
| GET    | /api/v1/reportes/vencimientos-proximos     | Vencimientos en N dias                   |
| GET    | /api/v1/reportes/actividad                 | Feed de actividad reciente               |

### Pendiente para Sesion 3

1. Integracion real con S3 (PDFs hoy van a C:\tmp\dolibarr_pdfs)
2. Probar sincronizacion con un Dolibarr real (DOLIBARR_API_KEY hoy es placeholder)
3. Configurar webhook real de Slack + API key de Resend (hoy ambos son placeholder)
4. Frontend Next.js que consuma estos 25 endpoints
5. Tests end-to-end del worker procesar_pdf con un PDF real
6. Tests para el motor de reglas contables
7. Ampliar parsers OCR (DECLARACION_GANANCIAS, SUSS detallado, IIBB ARBA/AGIP)
8. Logs estructurados con structlog en lugar de print
9. Hardening: validacion python-magic en subida de PDFs, validacion de tamano max, etc.
10. Health check extendido: verificar DB + Redis + Dolibarr

## Pendiente para Sesion 2

1. Importacion real de extractos bancarios (CSV / OFX / XLS) en app/workers/bank_tasks.py
2. Endpoints REST para movimientos bancarios y conciliacion manual
3. Integracion real con S3 (actualmente los PDFs se guardan en C:\tmp\dolibarr_pdfs)
4. Verificar y probar la sincronizacion con un Dolibarr real (actualmente DOLIBARR_API_KEY es placeholder)
5. Implementar notificaciones (Resend, Slack webhook)
6. Tests adicionales:
   - Tests integracion para endpoints de documentos
   - Tests end-to-end del worker procesar_pdf con un PDF real
   - Tests para el motor de reglas contables
7. Ampliar parsers OCR (DECLARACION_GANANCIAS, SUSS detallado, IIBB ARBA/AGIP)
8. Rate-limiting con slowapi en endpoints publicos (login, refresh)
9. Logs estructurados con structlog en lugar de print

## Notas importantes

- Python 3.14.5 + Windows 11 tiene una incompatibilidad con asyncpg cuando se reutilizan conexiones entre tests; se solucio usando NullPool cuando se detecta PYTEST_CURRENT_TEST en el entorno.
- bcrypt 5.x rompe passlib 1.7.4 (`module 'bcrypt' has no attribute '__about__'`). Se fijo bcrypt==4.0.1.
- easyocr y PyMuPDF NO se instalaron explicitamente; el motor OCR degrada elegantemente y solo usa la extraccion nativa de pdfplumber. Para PDFs escaneados habria que `py -m pip install easyocr pymupdf` (descarga modelos ~64MB la primera vez).
- python-magic-bin se instalo OK pero no se usa todavia; quedo disponible para validacion futura por content-type real.
- Celery worker bajo Windows requiere `--pool=solo` (no soporta prefork).

---

## Sesion 4 — Bugfix + Deploy

- ✅ [S4-BUG 1] Event loop fix en workers — reemplazado asyncio.run() por _ejecutar_async() con loop nuevo por ejecucion en pdf_tasks.py y reconcile_tasks.py
- ✅ [S4-BUG 2] Swagger con boton Authorize — custom_openapi() con BearerAuth SecurityScheme en main.py
- ✅ [S4-BUG 3] Token extendido a 1440 minutos (24h) en desarrollo — .env actualizado
- ✅ [S4-CORS] CORS ampliado a puertos 3000-3003 + soporte FRONTEND_URL para produccion
- ✅ [S4-CONFIG] config.py acepta DATABASE_URL de Railway (reemplaza postgres:// por postgresql+asyncpg://)
- ✅ [S4-HEALTH] /health extendido — verifica DB y Redis, retorna estado degradado si algo falla
- ✅ [S4-DEPLOY-B] Archivos de deploy backend creados: Procfile, railway.json, nixpacks.toml, requirements.txt (84 deps), .gitignore, railway.env.example
- ✅ [S4-DEPLOY-F] Archivos de deploy frontend creados: vercel.json, .env.production, next.config.ts con headers de seguridad
- ✅ [S4-GIT-B] git init + commit inicial backend (69786bf)
- ✅ [S4-GIT-F] git init + commit inicial frontend
- ✅ [S4-TESTS] 24/24 tests siguen pasando despues de todos los cambios
- ✅ [S4-DEPLOY-DOC] DEPLOY.md creado con instrucciones paso a paso para Railway + Vercel

## Estado final del proyecto

### Tests
24/24 pasando (2.78s)

### Comandos para desarrollo local

```powershell
# Terminal 1 — Backend
cd C:\Users\fede\Documents\automatizaciondolibar
.\venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — Worker Celery
.\venv\Scripts\Activate.ps1
py -m celery -A app.workers.celery_app worker --loglevel=info --pool=solo --without-heartbeat --without-gossip --without-mingle

# Terminal 3 — Frontend
cd C:\proyectos\dolibarr-frontend
npm run dev -- --port 3002
```

### URLs locales
- Frontend: http://localhost:3002
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs (con boton Authorize)
- Login: admin@demo.com / Admin1234!

### Pendiente para conectar Dolibarr real
1. Subir repos a GitHub
2. Deploy backend en Railway (ver DEPLOY.md)
3. Deploy frontend en Vercel (ver DEPLOY.md)
4. Obtener API key real de Dolibarr y actualizar variable en Railway
5. Conectar Slack webhook y Resend para notificaciones reales

## Sesión 5 — Conciliación automática de facturas a clientes

- ✅ [S5-PASO 1] Archivos existentes leídos
- ✅ [S5-PASO 2] Motor de matching invoice_matcher.py creado
- ✅ [S5-PASO 3] Dolibarr invoices.py actualizado con obtener_facturas_pendientes y registrar_pago_factura
- ✅ [S5-PASO 4] bank_tasks.py implementado con task conciliar_facturas_clientes
- ✅ [S5-PASO 5] banking/service.py dispara conciliación después de importar
- ✅ [S5-PASO 6] Endpoint GET /api/v1/bancario/facturas-pendientes agregado
- ✅ [S5-PASO 7] Tests del matcher creados y pasando
- ✅ [S5-PASO 8] 29/29 tests pasando
- ✅ [S5-PASO 9] Commit y push a GitHub

### Cómo funciona
1. Usuario importa CSV del Banco Galicia en /bancario
2. El sistema detecta los créditos (cobros de clientes)
3. Celery worker busca facturas pendientes en Dolibarr
4. Cruza por monto (60%) + nombre del cliente en descripción (30%) + fecha (10%)
5. Score >= 0.80 → marca la factura como PAGADA en Dolibarr automáticamente
6. Score 0.60-0.79 → muestra sugerencia para confirmar manualmente

### Pendiente para Sesión 6
- Importar facturas de venta desde AFIP via web services (wsfe)
- Importar movimientos bancarios directo a Dolibarr con cuenta contable asignada
- UI para ver facturas pendientes y matches sugeridos

## Sesión 6 — Reglas contables reales + sync con Dolibarr

- ✅ [S6-PASO 1] reglas_galicia.py creado: PLAN_DE_CUENTAS completo (70+ cuentas) + 29 reglas contables con prioridad, tipo, patrones y función clasificar_movimiento()
- ✅ [S6-PASO 2] base.py actualizado: MovimientoBancarioParsado incluye campos opcionales codigo_cuenta, nombre_cuenta, regla_aplicada
- ✅ [S6-PASO 2] csv_parser.py actualizado: llama a clasificar_movimiento() en cada fila y popula los campos contables
- ✅ [S6-PASO 3] dolibarr/client.py: nuevo método crear_movimiento_bancario() — POST /bankaccounts/{id}/lines
- ✅ [S6-PASO 4] bank_tasks.py: nueva Celery task sincronizar_movimientos_dolibarr() — reemplaza el proceso manual de 3.000 registros del cliente
- ✅ [S6-PASO 5] banking/service.py: dispara sincronización para TODOS los movimientos (no solo créditos) tras cada importación
- ✅ [S6-PASO 6] banking.py: endpoint POST /api/v1/bancario/clasificar para probar clasificación contable
- ✅ [S6-PASO 7] tests/unit/test_reglas_galicia.py: 29 tests unitarios cubriendo todas las reglas
- ✅ [S6-PASO 8] 58/58 tests pasando (29 previos + 29 nuevos)
- ✅ [S6-PASO 9] Commit cf16b61 pusheado a GitHub

### Las 29 reglas implementadas

| Prioridad | Regla | Cuenta |
|-----------|-------|--------|
| 10 | Impuesto débito Ley 25413 | 5.5.02 |
| 11 | Impuesto crédito Ley 25413 | 1.1.3.401 |
| 12 | IIBB SIRCREB | 1.1.3.204 |
| 13 | IIBB general | 5.5.01 |
| 14 | Percepción IVA | 1.1.3.106 |
| 15 | IVA bancario | 2.1.3.101 |
| 16 | Percepción RG 5617/24 | 1.1.3.205 |
| 17 | Impuesto de sellos | 5.5.04 |
| 18 | Intereses saldos deudores | 5.4.02 |
| 20 | Transferencia a AFIP | 5.4.01 |
| 30 | Cobro de cliente local | 4.1.05 |
| 31 | ECHEQ cobrado | 4.1.05 |
| 32 | Cobro del exterior | 4.2.01 |
| 33 | Anticipo de cliente | 2.1.1.201 |
| 40 | Pago a proveedor (TRF) | 5.1.01 |
| 41 | Pago proveedor Galicia | 5.1.01 |
| 42 | Alquiler | 5.2.04 |
| 43 | Seguro | 5.2.16 |
| 50 | Sueldos | 5.2.01 |
| 51 | SUSS | 2.1.2.102 |
| 52 | Honorarios | 5.2.03 |
| 60 | Suscripción FIMA | 1.1.5.102 |
| 61 | Rescate FIMA | 1.1.5.102 |
| 62 | Plazo fijo | 1.1.5.101 |
| 70 | Comisiones bancarias | 5.4.03 |
| 80 | Compra débito/tarjeta | 5.2.15 |
| 81 | Débito automático servicios | 5.2.18 |
| 82 | Pago de servicios | 5.2.18 |
| 83 | Pago Visa empresa | 5.2.15 |
| 90 | Diferencia de cambio | 5.6.01 |
| 999 | Fallback sin clasificar | 6.0 |

### Nota para producción

`bankaccount_id=1` en sincronizar_movimientos_dolibarr debe reemplazarse con el ID real
de la cuenta Galicia en el Dolibarr del cliente. Obtenerlo via GET /bankaccounts en la API
de Dolibarr usando la DOLIBARR_API_KEY del cliente.
