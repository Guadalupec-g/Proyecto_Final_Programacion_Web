# InfoMundi/backend/main.py
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from sqlalchemy.orm import Session
from sqlalchemy import text

from pydantic import BaseModel, HttpUrl, Field, validator
import pandas as pd
import math
import time
import os
from dotenv import load_dotenv

from .database import SessionLocal, engine
from .models import Favorito, Base
from .etl_pipeline import run_etl

# -------------------- Config & Seguridad --------------------
load_dotenv()

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = (
    [o.strip() for o in allowed_origins_env.split(",")] if allowed_origins_env != "*" else ["*"]
)
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*")  # p.ej. "localhost,mi-dominio.com"
TRUSTED_HOSTS = (
    [h.strip() for h in ALLOWED_HOSTS.split(",")] if ALLOWED_HOSTS != "*" else ["*"]
)

app = FastAPI(title="InfoMundi API")

# Forzar HTTPS (prod, detrás de Nginx con TLS)
if os.getenv("FORCE_HTTPS", "false").lower() == "true":
    app.add_middleware(HTTPSRedirectMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Trusted hosts (mitiga Host header attacks)
if TRUSTED_HOSTS != ["*"]:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=TRUSTED_HOSTS)

# -------------------- DB: crear tablas --------------------
Base.metadata.create_all(bind=engine)

# -------------------- Startup / Shutdown --------------------
@app.on_event("startup")
def wait_for_db_and_start_scheduler():
    # Espera DB lista
    for i in range(30):  # ~60s
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ DB lista")
            break
        except Exception as e:
            print(f"⏳ DB no lista ({e}). Reintento {i+1}/30")
            time.sleep(2)
    else:
        raise RuntimeError("❌ DB no estuvo lista a tiempo")

    # Iniciar scheduler (cada 5 min). Evita duplicar con --reload.
    from apscheduler.schedulers.background import BackgroundScheduler
    global _scheduler
    if "_scheduler" not in globals() or _scheduler is None:
        _scheduler = BackgroundScheduler()
        _scheduler.add_job(run_etl, "interval", minutes=5)
        _scheduler.start()
        print("⏱️  Scheduler iniciado (ETL cada 5 min)")

@app.on_event("shutdown")
def shutdown_event():
    global _scheduler
    try:
        if _scheduler:
            _scheduler.shutdown()
            print("🛑 Scheduler detenido")
    except NameError:
        pass

# -------------------- Dependencia de sesión --------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------- Modelos de request --------------------
class FavoritoCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=60)
    comentario: str = Field(..., min_length=1, max_length=280)
    imagen_url: HttpUrl

    @validator("nombre")
    def _nonempty(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("El nombre no puede estar vacío")
        return v

class FavoritoUpdate(BaseModel):
    nombre: str | None = Field(None, min_length=2, max_length=60)
    comentario: str | None = Field(None, min_length=1, max_length=280)
    imagen_url: HttpUrl | None = None

# -------------------- FAVORITOS CRUD --------------------
@app.post("/favoritos")
def crear_favorito(favorito: FavoritoCreate, db: Session = Depends(get_db)):
    nuevo = Favorito(**favorito.dict())
    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    # Insertar también en raw_data para ETL
    with engine.connect() as conn:
        insert_raw = text("""
            INSERT INTO raw_data (nombre, pais, fecha, valor, fuente)
            VALUES (:nombre, :pais, NOW(), :valor, :fuente)
        """)
        conn.execute(insert_raw, {
            "nombre": favorito.nombre,
            "pais": favorito.nombre,
            "valor": 0.0,
            "fuente": "favorito"
        })
        conn.commit()
    return nuevo

@app.get("/favoritos")
def listar_favoritos(db: Session = Depends(get_db)):
    return db.query(Favorito).all()

@app.get("/favoritos/{favorito_id}")
def obtener_favorito(favorito_id: int, db: Session = Depends(get_db)):
    obj = db.get(Favorito, favorito_id)
    if not obj:
        return JSONResponse(status_code=404, content={"detail": "No encontrado"})
    return obj

@app.put("/favoritos/{favorito_id}")
def actualizar_favorito(favorito_id: int, cambios: FavoritoUpdate, db: Session = Depends(get_db)):
    obj = db.get(Favorito, favorito_id)
    if not obj:
        return JSONResponse(status_code=404, content={"detail": "No encontrado"})
    data = cambios.dict(exclude_unset=True)
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@app.delete("/favoritos/{favorito_id}")
def eliminar_favorito(favorito_id: int, db: Session = Depends(get_db)):
    obj = db.get(Favorito, favorito_id)
    if not obj:
        return JSONResponse(status_code=404, content={"detail": "No encontrado"})
    db.delete(obj)
    db.commit()
    return {"mensaje": "Eliminado"}

# -------------------- PIPELINE ETL --------------------
@app.post("/api/pipeline/run")
def ejecutar_pipeline():
    log = run_etl()
    return {"mensaje": "ETL ejecutado correctamente", "log": log}

@app.get("/api/cleaned_data")
def obtener_datos_limpios():
    # reutiliza engine de database.py
    with engine.connect() as connection:
        df = pd.read_sql(text("SELECT * FROM cleaned_data"), connection)

    # Normalizar NaN/inf -> None
    registros = []
    for _, row in df.iterrows():
        registros.append({
            "id": int(row["id"]) if row.get("id") is not None and not pd.isna(row["id"]) else None,
            "nombre": None if pd.isna(row.get("nombre")) else row.get("nombre"),
            "pais": None if pd.isna(row.get("pais")) else row.get("pais"),
            "fecha": (
                row["fecha"].strftime("%Y-%m-%d")
                if (row.get("fecha") is not None and not pd.isna(row["fecha"]))
                else None
            ),
            "valor": (
                None if (
                    row.get("valor") is None or pd.isna(row["valor"]) or
                    (isinstance(row.get("valor"), float) and math.isinf(row["valor"]))
                )
                else float(row["valor"])
            ),
            "fuente": None if pd.isna(row.get("fuente")) else row.get("fuente"),
        })
    return JSONResponse(content=registros)

# -------------------- Health --------------------
@app.get("/health")
def health():
    return {"status": "ok"}
