# InfoMundi – FastAPI + MySQL + ETL (pandas) + Prefect + Docker

Proyecto web que expone un API con FastAPI, persiste datos en MySQL, ejecuta un pipeline ETL con pandas, lo orquesta con Prefect y sirve un frontend estático (HTML/CSS/JS). Incluye ejecución local y por Docker Compose.

# Objetivos del entregable

- Backend con FastAPI (CRUD y endpoints de negocio).

- Persistencia en MySQL con SQLAlchemy y script inicial.

- ETL con pandas que genera respaldos (CSV y JSON).

- Orquestación con Prefect (deployment y schedule).

- Frontend consumiendo el API.

- Contenerización con Docker Compose (db + api + web).

- Documentación clara de instalación, ejecución y troubleshooting.

# Tecnologías

- Backend: FastAPI, SQLAlchemy, Uvicorn

- Base de datos: MySQL 8

- ETL: pandas

- Orquestación: Prefect 3

- Frontend: HTML, CSS, JavaScript

- Contenedores: Docker y Docker Compose

- Otros: python-dotenv, APScheduler (opcional)

# Estructura del proyecto

proyecto_final_programacion_web/
├─ InfoMundi/
│  ├─ backend/
│  │  ├─ main.py               # FastAPI: endpoints, CORS, startup (espera DB)
│  │  ├─ models.py             # Modelos SQLAlchemy
│  │  ├─ database.py           # Engine/Session + .env
│  │  ├─ etl_pipeline.py       # run_etl(): lectura, limpieza, respaldos
│  │  ├─ crear_infomundi.sql   # Script SQL de creación inicial
│  │  └─ backups/              # raw_backup_*.csv, cleaned_backup_*.csv, etl_log_*.json
│  ├─ frontend/
│  │  ├─ index.html
│  │  ├─ styles.css
│  │  └─ script.js             # fetch al API
│  └─ requirements.txt
├─ pipeline/
│  └─ prefect_flow.py          # Flow: etl_flow (llama backend.etl_pipeline.run_etl)
├─ docker-compose.yml          # db + api + web (nginx)
├─ Dockerfile                  # imagen del servicio api
├─ .env                        # variables (no subir al repo)
└─ README.md

# Variables de entorno

Cree un archivo .env en la raíz (junto a docker-compose.yml). No lo suba al repositorio.

# Para Docker
MYSQL_ROOT_PASSWORD=<TU_PASSWORD>
MYSQL_DATABASE=infomundiF
ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080

# Para correr local (sin Docker)
DATABASE_URL=mysql+pymysql://root:<TU_PASSWORD>@localhost:3306/infomundiF


# Notas:

El backend lee DATABASE_URL desde .env en local y desde variables del compose en contenedor.

Si su contraseña contiene caracteres especiales (@ : / # % & +), codifíquelos en la URL (ej.: @ → %40, ! → %21).

Ejecución local (sin Docker)

Crear entorno virtual e instalar dependencias:

python -m venv venv
source venv/bin/activate
pip install -r InfoMundi/requirements.txt


Asegurar MySQL y la BD infomundiF. Para inicializar desde SQL:

mysql -uroot -p < InfoMundi/backend/crear_infomundi.sql

# -----------------------------------------------------------

# Levantar el backend:

cd InfoMundi
uvicorn backend.main:app --reload
# Swagger: http://127.0.0.1:8000/docs


# Frontend (dos alternativas):

Live Server (VSCode): abrir
http://127.0.0.1:5500/InfoMundi/frontend/index.html

Servir desde FastAPI (opcional, agregar a backend/main.py):

from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


Luego abrir http://127.0.0.1:8000/.

# Notas:

Para Live Server, considere añadir http://127.0.0.1:5500 a ALLOWED_ORIGINS en .env si usa CORS restringido.

Si desea que / redirija a Swagger, agregue:

from starlette.responses import RedirectResponse
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

# Ejecución con Docker Compose

Recomendado para la demo final (sirve también el frontend por Nginx en 8080).

Verifique .env (arriba).

docker-compose.yml con healthcheck y dependencia de DB:

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-infomundiF}
    ports:
      - "3306:3306"          # si choca con MySQL local: "3307:3306"
    volumes:
      - db_data:/var/lib/mysql
      - ./InfoMundi/backend/crear_infomundi.sql:/docker-entrypoint-initdb.d/1_schema.sql
    healthcheck:
      test: ["CMD-SHELL", "mysqladmin ping -h localhost -p$${MYSQL_ROOT_PASSWORD} || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 30

  api:
    build: .
    environment:
      DATABASE_URL: mysql+pymysql://root:${MYSQL_ROOT_PASSWORD:-root}@db:3306/${MYSQL_DATABASE:-infomundiF}
      ALLOWED_ORIGINS: http://localhost:8080,http://127.0.0.1:8080
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./InfoMundi/backend/backups:/app/InfoMundi/backend/backups

  web:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./InfoMundi/frontend:/usr/share/nginx/html:ro

volumes:
  db_data:


# Levantar limpio y construir:

docker compose down -v
docker compose up --build


# Probar:

API: http://localhost:8000/docs

Frontend: http://localhost:8080

# Notas:

El backend incluye una espera en startup que verifica la DB con pings antes de exponer el API.

Si el puerto 3306 está ocupado por un MySQL local, cambie a 3307:3306 en db.ports. Dentro de Docker, el API sigue usando db:3306.

Orquestación con Prefect (flow, deployment y schedule)

El ETL también se puede programar con Prefect.

Configurar el CLI para la UI local:

prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api


Iniciar servidor/UI en una terminal:

prefect server start
# UI: http://127.0.0.1:4200


En otra terminal (con venv) y desde la raíz:

export PYTHONPATH=.
prefect work-pool create -t process infomundi-pool

prefect deploy pipeline/prefect_flow.py:etl_flow \
  -n infomundi-deployment \
  --cron "*/5 * * * *" \
  -p infomundi-pool \
  -q default

# Si pregunta por almacenamiento remoto del código, responda: n


# Iniciar el worker:

export PYTHONPATH=.
prefect worker start -p infomundi-pool


Ejecutar manualmente (opcional):

prefect deployment run "infomundi-etl/infomundi-deployment"


Ver corridas en la UI (Runs). Los archivos de respaldo se guardan en InfoMundi/backend/backups/.

# Endpoints principales

GET /favoritos – lista favoritos

POST /favoritos – crea favorito

{
  "nombre": "Costa Rica",
  "comentario": "Me gusta",
  "imagen_url": "https://example.com/bandera.png"
}


GET /favoritos/{id} – obtiene por id

PUT /favoritos/{id} – actualiza

DELETE /favoritos/{id} – elimina

POST /api/pipeline/run – ejecuta ETL manualmente

GET /api/cleaned_data – devuelve datos limpios (para tabla del front)

# Documentación interactiva: /docs (Swagger) y /redoc.

# Frontend

Docker: http://localhost:8080

Local con Live Server: http://127.0.0.1:5500/InfoMundi/frontend/index.html

Asegúrese de que script.js apunte al host correcto del API (por ejemplo, http://localhost:8000).

# ETL y respaldos

run_etl() en backend/etl_pipeline.py:

Lee datos “raw” desde la base de datos (consulta SQL).

Aplica limpieza y normalización con pandas.

Genera respaldos en backend/backups/:

raw_backup_YYYYMMDD_HHMMSS.csv

cleaned_backup_YYYYMMDD_HHMMSS.csv

etl_log_YYYYMMDD_HHMMSS.json (métricas de ejecución)

# Se ejecuta:

Manualmente: POST /api/pipeline/run

Programado: con Prefect según el cron del deployment.

Pruebas rápidas (curl)
# crear
curl -X POST http://localhost:8000/favoritos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"CR","comentario":"Me gusta","imagen_url":"https://ejemplo/img.png"}'

# listar
curl http://localhost:8000/favoritos

# correr ETL
curl -X POST http://localhost:8000/api/pipeline/run

# datos limpios
curl http://localhost:8000/api/cleaned_data

# Solución de problemas

Puerto 8000 en uso (Address already in use)
Cierre Uvicorn local si usa Docker, o lance en otro puerto:

uvicorn backend.main:app --reload --port 8001


Para cerrar procesos en macOS:

lsof -ti tcp:8000 | xargs kill -9


Frontend 8080 no carga (ERR_CONNECTION_REFUSED)
Asegure docker compose up en ejecución (servicio web encendido).

CORS desde 8080 o 5500
Agregue orígenes en .env:

ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080,http://127.0.0.1:5500


API se cae al arrancar con Docker (DB no lista)
Este compose incluye healthcheck y el backend espera a la DB en startup. Si modificó algo y vuelve a suceder:

docker compose logs -f db
docker compose logs -f api


MySQL local ocupando 3306
Cambie mapeo a 3307:3306 en db.ports. Dentro de Docker, el API usa db:3306 y no requiere cambios.

# Checklist de cumplimiento

Repositorio con frontend/, backend/, pipeline/ y script SQL.

.env presente localmente y excluido por .gitignore.

FastAPI con CRUD de favoritos y endpoints de negocio.

MySQL con SQLAlchemy y script de creación inicial.

ETL en pandas con respaldos CSV/JSON periódicos o manuales.

Prefect: flow, deployment y schedule activo; worker corriendo.

Frontend consumiendo el API.

Docker Compose con db + api + web, healthcheck y dependencias.

Documentación de instalación, ejecución y troubleshooting.

# Requisitos y versiones

Python 3.12

Docker Desktop (recomendado)

Prefect 3.x (CLI)

MySQL 8 (si corre sin Docker)