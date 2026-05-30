# Instrucciones de Deploy

## Backend en Railway

### 1. Subir el código a GitHub

```powershell
# Crear repo en github.com → New repository → "dolibarr-backend"
git remote add origin https://github.com/TU_USUARIO/dolibarr-backend.git
git push -u origin main
```

### 2. Crear proyecto en Railway

1. Ir a https://railway.app → **New Project**
2. **Deploy from GitHub repo** → seleccionar `dolibarr-backend`
3. Railway detecta Python y usa Nixpacks automáticamente

### 3. Agregar base de datos y Redis

En el proyecto Railway:
- Click **New** → **Database** → **Add PostgreSQL**
- Click **New** → **Database** → **Add Redis**
- Railway inyecta `DATABASE_URL` y `REDIS_URL` automáticamente

### 4. Configurar variables de entorno

En el servicio del backend → **Variables** → agregar todo lo de `railway.env.example`:

```
SECRET_KEY=<generar con: python -c "import secrets; print(secrets.token_hex(32))">
ENVIRONMENT=production
DOLIBARR_URL=https://dolibarr.tuempresa.com
DOLIBARR_API_KEY=tu_clave_real
FRONTEND_URL=https://dolibarr-frontend.vercel.app
ACCESS_TOKEN_EXPIRE_MINUTES=15
```

Las demás variables (DB, Redis) las provee Railway automáticamente.

### 5. Correr las migrations

En Railway → tu servicio → **Settings** → **Deploy** → **Start Command** (temporalmente):
```
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```
Después del primer deploy exitoso, volver al comando original:
```
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 6. Verificar

```
https://tu-servicio.railway.app/health   → {"estado": "ok", "servicios": {...}}
https://tu-servicio.railway.app/docs     → Swagger con botón Authorize
```

---

## Frontend en Vercel

### 1. Subir a GitHub

```powershell
cd C:\proyectos\dolibarr-frontend
git remote add origin https://github.com/TU_USUARIO/dolibarr-frontend.git
git push -u origin main
```

### 2. Crear proyecto en Vercel

1. Ir a https://vercel.com → **New Project**
2. Importar `dolibarr-frontend` desde GitHub
3. En **Environment Variables** agregar:
   - `NEXT_PUBLIC_API_URL` = `https://tu-servicio.railway.app`
4. Click **Deploy**

### 3. Actualizar CORS en Railway

Una vez que Vercel asigne la URL (ej: `https://dolibarr-frontend.vercel.app`):
- En Railway → Variables → `FRONTEND_URL` = esa URL
- El backend se recarga automáticamente

---

## Conectar Dolibarr real

1. En Dolibarr: **Configuración → Sistema → API/REST → Generar clave**
2. En Railway → Variables:
   - `DOLIBARR_URL` = URL de la instancia Dolibarr
   - `DOLIBARR_API_KEY` = clave generada
3. El backend se reconecta sin necesidad de redeploy

---

## Verificar flujo completo

1. `https://tu-backend.railway.app/health` → `{"estado": "ok"}`
2. `https://tu-frontend.vercel.app` → pantalla de login
3. Login con `admin@demo.com` / `Admin1234!`
4. Subir un PDF real de AFIP (VEP de IVA)
5. Verificar que clasifica automáticamente con cuenta 2.01.001
6. Aprobar el documento
7. Importar extracto bancario CSV
8. Correr conciliación → debe sugerir match con score HIGH

---

## Comandos para desarrollo local

```powershell
# Terminal 1 — Backend
cd C:\Users\fede\Documents\automatizaciondolibar
.\venv\Scripts\Activate.ps1
py -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — Worker Celery
cd C:\Users\fede\Documents\automatizaciondolibar
.\venv\Scripts\Activate.ps1
py -m celery -A app.workers.celery_app worker --loglevel=info --pool=solo --without-heartbeat --without-gossip --without-mingle

# Terminal 3 — Frontend
cd C:\proyectos\dolibarr-frontend
npm run dev -- --port 3002
```

URLs locales:
- Frontend: http://localhost:3002
- Backend API: http://localhost:8000
- Swagger: http://localhost:8000/docs
