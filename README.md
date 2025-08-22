InfoMundi — FastAPI + MySQL + ETL (pandas) + Prefect + Nginx/HTTPS + Docker Compose
Descripción

Proyecto full-stack que:

expone una API en FastAPI (CRUD de favoritos, healthcheck, ETL).

guarda datos en MySQL.

ejecuta un pipeline ETL con pandas (raw_data → cleaned_data, backups CSV y logs JSON).

orquesta el ETL con Prefect 2.x (UI local y ejecución manual/automática).

sirve un frontend estático (busca países con la API pública REST Countries, guarda favoritos, consume cleaned_data).

publica front+API detrás de Nginx con HTTPS (certificado self-signed local) y cabeceras seguras (CSP, HSTS, etc.).

se levanta con Docker Compose.

incluye CI (lint + build) y base para CD (despliegue a staging opcional) en GitHub Actions.

Demo local — Puertos y URLs
Servicio	URL local	Puerto host → contenedor
Frontend (HTTPS)	https://localhost:8443
	8443:8443
Frontend (HTTP redirige)	http://localhost:8081
	8081:8080
API FastAPI	http://localhost:8000/docs
	8000:8000
Prefect UI	http://127.0.0.1:4200
	Local (sin docker)
MySQL	127.0.0.1:3307	3307:3306

Nota: Los navegadores mostrarán aviso de “conexión no privada” por usar un certificado self-signed. En local: Avanzado → Continuar.

Arquitectura
[Frontend] --HTTPS--> [Nginx]
                        |--> /api → FastAPI (uvicorn)
                        |--> /docs | /redoc → FastAPI
                        |--> estáticos (index.html, script.js, styles.css)
[FastAPI] --SQLAlchemy--> [MySQL]
ETL (pandas) <------> backups CSV/JSON (montados al host)
Prefect (flows/tasks) ← orquesta ejecución ETL

Tecnologías

FastAPI: tipado, rendimiento y docs Swagger automáticas.

MySQL: motor SQL popular, dockerizable.

pandas: limpieza y transformaciones tabulares simples.

Prefect: orquestación de tasks/flows con UI y agentes.

Nginx: TLS, estáticos y reverse proxy seguro.

Docker Compose: desarrollo reproducible.

Estructura del repositorio
.
├─ .github/workflows/ci-cd.yml       # Lint + Build (base para Deploy opcional)
├─ compose.staging.yml               # Compose para staging (opcional)
├─ nginx.staging.conf                # Configuración Nginx staging (opcional)
├─ InfoMundi/
│  ├─ backend/
│  │  ├─ main.py                     # API FastAPI (CRUD + ETL endpoints)
│  │  ├─ database.py                 # Conexión SQLAlchemy
│  │  ├─ models.py                   # ORM (Favorito, raw_data, cleaned_data)
│  │  ├─ etl_pipeline.py             # Lógica ETL
│  │  └─ crear_infomundi.sql         # Creación de tablas
│  └─ frontend/
│     ├─ index.html                  # UI (responsive, modo oscuro)
│     ├─ script.js                   # Llama REST Countries y API local
│     └─ styles.css                  # Estilos
├─ pipeline/
│  └─ prefect_flow.py                # Flow Prefect para run_etl()
├─ docker-compose.yml                # Stack local (db, api, nginx)
├─ nginx.conf                        # HTTPS, CSP, proxy /api
├─ Dockerfile                        # Imagen del backend
├─ requirements.txt                  # Dependencias
├─ prefect.yaml                      # Config Prefect local
├─ .env.example                      # Variables de entorno de ejemplo
├─ .gitignore / .prefectignore       # Ignorar venv, certs, backups, .env
└─ tests/                            # (opcional) pruebas unitarias
   └─ test_api.py

Variables de entorno

Archivo .env (no subir al repo):

# Backend
DATABASE_URL=mysql+pymysql://root:<TU_PASS>@db:3306/infomundiF
ALLOWED_ORIGINS=http://localhost:8081,http://127.0.0.1:8081,http://127.0.0.1:5500
ALLOWED_HOSTS=localhost,127.0.0.1
FORCE_HTTPS=false

# MySQL
MYSQL_ROOT_PASSWORD=<TU_PASS>
MYSQL_DATABASE=infomundiF

Puesta en marcha (Docker Compose)

Generar certificados self-signed (una sola vez):

mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/privkey.key -out certs/fullchain.crt \
  -days 365 -subj "/CN=localhost"


Levantar la stack:

docker compose up --build


Abrir en navegador:

Frontend: https://localhost:8443

API: http://localhost:8000/docs

Apagar:

docker compose down

API — Endpoints principales

GET /health → estado ok

POST /favoritos → crea favorito (se inserta en raw_data)

GET /favoritos, GET/PUT/DELETE /favoritos/{id}

POST /api/pipeline/run → ejecuta ETL ahora

GET /api/cleaned_data → datos limpios

GET /docs → Swagger

GET /redoc → ReDoc

ETL

Archivo: InfoMundi/backend/etl_pipeline.py

Elimina filas vacías.

Limpieza de strings (strip, title).

País → uppercase.

Fecha → datetime, descarta inválidas.

Reemplaza NaN/±inf → None.

Trunca y recarga cleaned_data.

Backups en CSV y logs JSON.

Orquestación con Prefect

Archivo: pipeline/prefect_flow.py

# UI
prefect server start
# http://127.0.0.1:4200

# Ejecutar flow
python pipeline/prefect_flow.py


En la UI verás el run con estado Completed.

Nginx + Seguridad

Archivo: nginx.conf

HTTPS (8443) con cert local.

HTTP (8081) redirige a HTTPS.

Reverse proxy: /api → FastAPI, /docs y /redoc.

Headers seguros: HSTS, CSP, X-Frame-Options, etc.

CI/CD — GitHub Actions

Archivo: .github/workflows/ci-cd.yml

Lint (flake8).

(Opcional) tests (pytest).

Build & push Docker image.

Deploy a staging (opcional, requiere secretos SSH configurados).

Comandos útiles

Local sin docker:

uvicorn InfoMundi.backend.main:app --reload --port 8000
python -m http.server 5500 -d InfoMundi/frontend
prefect server start


Con docker:

docker compose up --build
docker compose logs -f api
docker compose down


MySQL CLI:

docker exec -it <db_container> mysql -uroot -p

Buenas prácticas

.gitignore evita subir .env, certs/, backups/, venv/.

.env.example sirve como plantilla segura.

Backups automáticos del ETL.

Prefect UI para monitoreo de pipelines.

Cabeceras seguras en Nginx.

CI/CD automático para validación de cambios.

¿Quieres que te lo prepare ya como archivo README.md listo para que lo copies/pegues en tu repo?

Tú dijiste:
sip
ChatGPT Plus

Perfecto, aquí te lo dejo ya listo como archivo README.md. Solo copia y pega en tu proyecto (en la raíz), y quedará con el formato limpio para que se vea bien en GitHub:

# InfoMundi — FastAPI + MySQL + ETL (pandas) + Prefect + Nginx/HTTPS + Docker Compose

## Descripción

Proyecto full-stack que:  
- expone una API en FastAPI (CRUD de favoritos, healthcheck, ETL).  
- guarda datos en MySQL.  
- ejecuta un pipeline ETL con pandas (`raw_data` → `cleaned_data`, backups CSV y logs JSON).  
- orquesta el ETL con Prefect 2.x (UI local y ejecución manual/automática).  
- sirve un frontend estático (busca países con la API pública REST Countries, guarda favoritos, consume `cleaned_data`).  
- publica front+API detrás de Nginx con HTTPS (certificado self-signed local) y cabeceras seguras (CSP, HSTS, etc.).  
- se levanta con Docker Compose.  
- incluye CI (lint + build) y base para CD (despliegue a staging opcional) en GitHub Actions.  

---

## Demo local — Puertos y URLs

| Servicio                | URL local                       | Puerto host → contenedor |
|--------------------------|---------------------------------|---------------------------|
| Frontend (HTTPS)        | https://localhost:8443          | 8443:8443                |
| Frontend (HTTP redirige)| http://localhost:8081           | 8081:8080                |
| API FastAPI             | http://localhost:8000/docs      | 8000:8000                |
| Prefect UI              | http://127.0.0.1:4200           | Local (sin docker)       |
| MySQL                   | 127.0.0.1:3307                  | 3307:3306                |

> Nota: Los navegadores mostrarán aviso de “conexión no privada” por usar un certificado self-signed. En local: Avanzado → Continuar.

---

## Arquitectura



[Frontend] --HTTPS--> [Nginx]
|--> /api → FastAPI (uvicorn)
|--> /docs | /redoc → FastAPI
|--> estáticos (index.html, script.js, styles.css)
[FastAPI] --SQLAlchemy--> [MySQL]
ETL (pandas) <------> backups CSV/JSON (montados al host)
Prefect (flows/tasks) ← orquesta ejecución ETL


---

## Tecnologías

- **FastAPI**: tipado, rendimiento y docs Swagger automáticas.  
- **MySQL**: motor SQL popular, dockerizable.  
- **pandas**: limpieza y transformaciones tabulares simples.  
- **Prefect**: orquestación de tasks/flows con UI y agentes.  
- **Nginx**: TLS, estáticos y reverse proxy seguro.  
- **Docker Compose**: desarrollo reproducible.  

---

## Estructura del repositorio



.
├─ .github/workflows/ci-cd.yml # Lint + Build (base para Deploy opcional)
├─ compose.staging.yml # Compose para staging (opcional)
├─ nginx.staging.conf # Configuración Nginx staging (opcional)
├─ InfoMundi/
│ ├─ backend/
│ │ ├─ main.py # API FastAPI (CRUD + ETL endpoints)
│ │ ├─ database.py # Conexión SQLAlchemy
│ │ ├─ models.py # ORM (Favorito, raw_data, cleaned_data)
│ │ ├─ etl_pipeline.py # Lógica ETL
│ │ └─ crear_infomundi.sql # Creación de tablas
│ └─ frontend/
│ ├─ index.html # UI (responsive, modo oscuro)
│ ├─ script.js # Llama REST Countries y API local
│ └─ styles.css # Estilos
├─ pipeline/
│ └─ prefect_flow.py # Flow Prefect para run_etl()
├─ docker-compose.yml # Stack local (db, api, nginx)
├─ nginx.conf # HTTPS, CSP, proxy /api
├─ Dockerfile # Imagen del backend
├─ requirements.txt # Dependencias
├─ prefect.yaml # Config Prefect local
├─ .env.example # Variables de entorno de ejemplo
├─ .gitignore / .prefectignore # Ignorar venv, certs, backups, .env
└─ tests/ # (opcional) pruebas unitarias
└─ test_api.py


---

## Variables de entorno

Archivo `.env` (no subir al repo):

```bash
# Backend
DATABASE_URL=mysql+pymysql://root:<TU_PASS>@db:3306/infomundiF
ALLOWED_ORIGINS=http://localhost:8081,http://127.0.0.1:8081,http://127.0.0.1:5500
ALLOWED_HOSTS=localhost,127.0.0.1
FORCE_HTTPS=false

# MySQL
MYSQL_ROOT_PASSWORD=<TU_PASS>
MYSQL_DATABASE=infomundiF

Puesta en marcha (Docker Compose)

Generar certificados self-signed (una sola vez):

mkdir -p certs
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout certs/privkey.key -out certs/fullchain.crt \
  -days 365 -subj "/CN=localhost"


Levantar la stack:

docker compose up --build


Abrir en navegador:

Frontend: https://localhost:8443

API: http://localhost:8000/docs

Apagar:

docker compose down

API — Endpoints principales

GET /health → estado ok

POST /favoritos → crea favorito (se inserta en raw_data)

GET /favoritos, GET/PUT/DELETE /favoritos/{id}

POST /api/pipeline/run → ejecuta ETL ahora

GET /api/cleaned_data → datos limpios

GET /docs → Swagger

GET /redoc → ReDoc

ETL

Archivo: InfoMundi/backend/etl_pipeline.py

Elimina filas vacías.

Limpieza de strings (strip, title).

País → uppercase.

Fecha → datetime, descarta inválidas.

Reemplaza NaN/±inf → None.

Trunca y recarga cleaned_data.

Backups en CSV y logs JSON.

Orquestación con Prefect

Archivo: pipeline/prefect_flow.py

# UI
prefect server start
# http://127.0.0.1:4200

# Ejecutar flow
python pipeline/prefect_flow.py


En la UI verás el run con estado Completed.

Nginx + Seguridad

Archivo: nginx.conf

HTTPS (8443) con cert local.

HTTP (8081) redirige a HTTPS.

Reverse proxy: /api → FastAPI, /docs y /redoc.

Headers seguros: HSTS, CSP, X-Frame-Options, etc.

CI/CD — GitHub Actions

Archivo: .github/workflows/ci-cd.yml

Lint (flake8).

(Opcional) tests (pytest).

Build & push Docker image.

Deploy a staging (opcional, requiere secretos SSH configurados).

Comandos útiles

Local sin docker:

uvicorn InfoMundi.backend.main:app --reload --port 8000
python -m http.server 5500 -d InfoMundi/frontend
prefect server start


Con docker:

docker compose up --build
docker compose logs -f api
docker compose down


MySQL CLI:

docker exec -it <db_container> mysql -uroot -p

Buenas prácticas

.gitignore evita subir .env, certs/, backups/, venv/.

.env.example sirve como plantilla segura.

Backups automáticos del ETL.

Prefect UI para monitoreo de pipelines.

Cabeceras seguras en Nginx.

CI/CD automático para validación de cambios.