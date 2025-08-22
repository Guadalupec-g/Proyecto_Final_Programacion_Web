# InfoMundi 🌍 — FastAPI + MySQL + ETL + Prefect + Nginx (HTTPS)

Explora países con una API pública, guarda favoritos y visualiza datos limpios generados por un pipeline ETL.
**Stack:** FastAPI, SQLAlchemy/MySQL, pandas, Prefect 2.x, Docker Compose, Nginx (TLS local).

---

## Tabla de contenido

* [Características](#características)
* [Estructura del repositorio](#estructura-del-repositorio)
* [Requisitos](#requisitos)
* [Variables de entorno](#variables-de-entorno)
* [Inicio rápido](#inicio-rápido)

  * [Opción A: Docker Compose](#opción-a--docker-compose)
  * [Opción B: API local + DB en contenedor](#opción-b--api-local--db-en-contenedor)
* [Probar la API y el ETL](#probar-la-api-y-el-etl)
* [Orquestación con Prefect 2.x](#orquestación-con-prefect-2x)
* [Nginx + HTTPS + Seguridad](#nginx--https--seguridad)
* [CI (demo) con GitHub Actions](#ci-demo-con-github-actions)
* [Comandos útiles](#comandos-útiles)
* [Troubleshooting](#troubleshooting)
* [Notas](#notas)

---

## Características

* **API pública:** `restcountries.com` para búsqueda por nombre.
* **Backend:** FastAPI + SQLAlchemy (endpoints CRUD de favoritos + endpoints ETL).
* **Base de datos:** MySQL 8 en contenedor.
* **ETL:** Limpia `raw_data` → `cleaned_data`, genera backups (CSV) y logs (JSON).
* **Orquestación:** Prefect 2.x (flow, work pool y UI).
* **Frontend estático:** HTML/CSS/JS (modo oscuro, UI simple).
* **Reverse proxy:** Nginx con HTTPS local (certificado autofirmado) y headers de seguridad (CSP incluida).
* **CI (demo):** GitHub Actions (lint + levantar staging con docker compose y health-check).

---

## Estructura del repositorio

```
.
├─ .github/workflows/ci-cd.yml     # Pipeline CI (demo)
├─ InfoMundi/
│  ├─ backend/
│  │  ├─ main.py                   # FastAPI app (CORS, seguridad, scheduler ETL)
│  │  ├─ etl_pipeline.py           # Lógica ETL (pandas)
│  │  ├─ database.py               # Conexión SQLAlchemy (DATABASE_URL)
│  │  ├─ models.py                 # Modelos/ORM
│  │  └─ crear_infomundi.sql       # Esquema inicial (tablas raw/cleaned/favoritos)
│  └─ frontend/
│     ├─ index.html                # Frontend estático
│     ├─ styles.css
│     └─ script.js
├─ pipeline/
│  └─ prefect_flow.py              # Flow Prefect (importa y ejecuta run_etl)
├─ docker-compose.yml              # Servicios: db + api + nginx
├─ nginx.conf                      # HTTPS + headers seguros + proxy /api
├─ Dockerfile                      # Imagen de la API
├─ requirements.txt                # Dependencias (API/ETL/Prefect)
├─ .env.example                    # Variables ejemplo (no subas .env real)
└─ certs/                          # (local) Llaves TLS autofirmadas (gitignored)
```

---

## Requisitos

* Docker y Docker Compose (para la opción A).
* Python 3.10+ y `venv` (solo si usarás la opción B).
* OpenSSL (para generar el certificado local).

---

## Variables de entorno

Crea un archivo `.env` en la **raíz** (NO lo subas a Git). Puedes basarte en `.env.example`:

```bash
# DB
MYSQL_ROOT_PASSWORD=LupeSecure_2025
MYSQL_DATABASE=infomundiF

# API
ALLOWED_ORIGINS=http://localhost:8081,https://localhost:8443,http://127.0.0.1:5500
ALLOWED_HOSTS=localhost,127.0.0.1
FORCE_HTTPS=false
```

**Nota:** `.env` está en `.gitignore`. Las credenciales no se subirán al repo.

---

## Inicio rápido

### Opción A — Docker Compose

1. Generar certificados locales (una sola vez):

```bash
mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/privkey.key -out certs/fullchain.crt \
  -days 365 -subj "/CN=localhost"
```

2. Levantar toda la stack:

```bash
docker compose up --build
```

3. Abrir el sitio:

* Frontend (por Nginx con HTTPS): `https://localhost:8443`
  Acepta el aviso del certificado autofirmado.
* API directa (FastAPI): `http://localhost:8000`
* MySQL (host): `127.0.0.1:3307` (user: `root`, pass: `${MYSQL_ROOT_PASSWORD}`)

> Si `8080` estaba ocupado, el compose ya mapea `8081:8080` y `8443:8443`.

---

### Opción B — API local (sin Docker) usando la DB del contenedor

1. Deja corriendo **solo** la base de datos (o todo el compose).
2. Crea un entorno virtual e instala dependencias:

```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Exporta la URL a la DB del contenedor (puerto 3307 del host):

```bash
export DATABASE_URL="mysql+pymysql://root:${MYSQL_ROOT_PASSWORD:-root}@127.0.0.1:3307/${MYSQL_DATABASE:-infomundiF}"
```

4. Corre FastAPI:

```bash
uvicorn InfoMundi.backend.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend: abre `InfoMundi/frontend/index.html` con Live Server o usa el Nginx del compose.

---

## Probar la API y el ETL

**Endpoints clave**

* `GET /favoritos`
* `POST /favoritos` (body: `{"nombre":"Canada","comentario":"Me gusta","imagen_url":"https://..."}`)
* `POST /api/pipeline/run` → ejecuta ETL ahora
* `GET /api/cleaned_data` → datos limpios

**Pruebas rápidas (curl)**

```bash
# Ejecutar ETL manualmente
curl -X POST http://localhost:8000/api/pipeline/run

# Ver tabla cleaned_data
curl http://localhost:8000/api/cleaned_data

# Crear un favorito
curl -X POST http://localhost:8000/favoritos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Canada","comentario":"Me gusta","imagen_url":"https://flagcdn.com/w320/ca.png"}'

# Listar favoritos
curl http://localhost:8000/favoritos
```

El ETL también corre automáticamente cada 5 min (APScheduler en `main.py`).

---

## Orquestación con Prefect 2.x

`pipeline/prefect_flow.py` importa `run_etl()` y lo expone como `etl_flow`.

### A) UI/servidor local de Prefect

En otra terminal:

```bash
# 1) Iniciar servidor + UI (http://127.0.0.1:4200)
prefect server start

# 2) (Opcional) apuntar el cliente al server local
prefect config set PREFECT_API_URL="http://127.0.0.1:4200/api"

# 3) Crear un Work Pool (tipo "process")
prefect work-pool create infomundi-pool --type process

# 4) Iniciar un worker escuchando ese pool
prefect worker start --pool infomundi-pool

# 5) Ejecutar el flow ad-hoc
python pipeline/prefect_flow.py
```

Visualiza el run: `http://127.0.0.1:4200/runs`.

### B) (Opcional) Deployment con schedule

```bash
prefect deployment build pipeline/prefect_flow.py:etl_flow \
  -n infomundi-deployment -p infomundi-pool -q default \
  -o pipeline/deployment.yaml --cron "*/5 * * * *"

prefect deployment apply pipeline/deployment.yaml
```

---

## Nginx + HTTPS + Seguridad

* Redirección `http://localhost:8081` → `https://localhost:8443`.
* Headers activos: **HSTS**, **X-Frame-Options**, **X-Content-Type-Options**, **Referrer-Policy**, **Permissions-Policy**.
* **CSP** (Content-Security-Policy) restrictiva; permite únicamente:

  * Recursos propios (`'self'`)
  * `restcountries.com` para fetch
  * Imágenes `https` + `flagcdn.com`
* Proxy `/api` → `api:8000` (servicio FastAPI del compose).

> Si cambias dominios/puertos, ajusta la **CSP** en `nginx.conf` y `ALLOWED_ORIGINS` en `.env`.

---

## CI (demo) con GitHub Actions

Ubicación: `.github/workflows/ci-cd.yml`

Incluye:

* `flake8` (lint).
* Levanta staging local con `docker compose` y valida que `/api/cleaned_data` responde.
* No publica imágenes a DockerHub (no es necesario para la demo).

---

## Comandos útiles

```bash
# Logs de la API (compose)
docker compose logs -f api

# Reconstruir todo
docker compose down
docker compose up --build

# Acceder a MySQL del contenedor desde el host
mysql -h 127.0.0.1 -P 3307 -u root -p
USE infomundiF;
SHOW TABLES;

# Ver backups generados por el ETL (mapeados al host)
ls -l InfoMundi/backend/backups
```

---

## Troubleshooting

* **Puertos 8443/8081 ocupados:** edita los mapeos en `docker-compose.yml`.
* **Navegador “inseguro”:** el certificado es autofirmado; usa *Advanced → Proceed*.
* **Swagger “Invalid host header”:** mitigado por proxy Nginx.
* **Prefect “connection refused”:** corre `prefect server start` y verifica `PREFECT_API_URL=http://127.0.0.1:4200/api`.
* **CORS desde Live Server:** usa `https://localhost:8443` (Nginx). `script.js` consume `/api/...` y el proxy resuelve.
* **Errores de conexión a MySQL:** confirma `DATABASE_URL`, el puerto `3307` y que el contenedor `db` esté *healthy*.
* **`docker compose up` falla en Apple Silicon:** asegúrate de usar imágenes multi-arch o habilita `platform: linux/amd64` si alguna dependencia lo requiere.

---

## Notas

* Este repositorio está pensado para **demo local**. No incluye hardening para producción ni despliegues remotos.
* Si deseas exponerlo públicamente, considera:

  * Renovación de certificados (no autofirmados).
  * Rotación de secretos y almacenes seguros.
  * Reverse proxy y WAF gestionados.
  * Observabilidad (logs, métricas y trazas).
  * Backups externos y política de retención.
