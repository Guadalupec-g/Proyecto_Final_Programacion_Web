# InfoMundi/backend/etl_pipeline.py
import json
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

# ✅ Reutiliza el engine configurado en database.py (lee DATABASE_URL del entorno)
from .database import engine

# Carpeta de backups (montada en docker-compose hacia tu host)
BASE_DIR = Path(__file__).resolve().parent
BACKUPS_DIR = BASE_DIR / "backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)


def run_etl():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- EXTRACCIÓN ---
    with engine.connect() as conn:
        # ⚠️ Ajusta el nombre de la tabla de origen si no es 'raw_data'
        df_raw = pd.read_sql(text("SELECT * FROM raw_data"), conn)
        registros_leidos = len(df_raw)

    # --- TRANSFORMACIÓN ---
    df_clean = df_raw.copy()

    if not df_clean.empty:
        # Limpiezas de ejemplo; ajusta a tus columnas reales
        df_clean = df_clean.dropna(how="all")
        if "nombre" in df_clean.columns:
            df_clean["nombre"] = (
                df_clean["nombre"].astype(str).str.strip().str.title()
            )
            df_clean = df_clean[df_clean["nombre"] != ""]
        if "pais" in df_clean.columns:
            df_clean["pais"] = df_clean["pais"].astype(str).str.upper()
        if "fecha" in df_clean.columns:
            df_clean["fecha"] = pd.to_datetime(df_clean["fecha"], errors="coerce")
            df_clean = df_clean.dropna(subset=["fecha"])

        # Reemplazos seguros
        df_clean = df_clean.replace([float("inf"), float("-inf")], None)
        df_clean = df_clean.where(pd.notnull(df_clean), None)

    registros_limpios = len(df_clean)

    # --- CARGA ---
    # Usa una transacción (engine.begin()) y evita commits manuales
    with engine.begin() as conn:
        # ⚠️ Ajusta el nombre de la tabla destino si no es 'cleaned_data'
        conn.execute(text("TRUNCATE TABLE cleaned_data"))

        if registros_limpios > 0:
            # Inserción vectorizada con executemany
            rows = []
            for _, row in df_clean.iterrows():
                rows.append(
                    {
                        "id": int(row["id"]) if row.get("id") not in (None, "") else None,
                        "nombre": row.get("nombre"),
                        "pais": row.get("pais"),
                        "fecha": (
                            row["fecha"].date()
                            if row.get("fecha") is not None
                            else None
                        ),
                        "valor": (
                            float(row["valor"])
                            if row.get("valor") not in (None, "")
                            else None
                        ),
                        "fuente": row.get("fuente"),
                    }
                )

            if rows:
                conn.execute(
                    text(
                        """
                        INSERT INTO cleaned_data (id, nombre, pais, fecha, valor, fuente)
                        VALUES (:id, :nombre, :pais, :fecha, :valor, :fuente)
                        """
                    ),
                    rows,
                )

    # --- BACKUPS ---
    raw_csv_path = BACKUPS_DIR / f"raw_backup_{ts}.csv"
    clean_csv_path = BACKUPS_DIR / f"cleaned_backup_{ts}.csv"

    df_raw.to_csv(raw_csv_path, index=False)
    if registros_limpios > 0:
        df_clean.to_csv(clean_csv_path, index=False)

    # --- LOG ---
    log_data = {
        "timestamp": ts,
        "registros_leidos": registros_leidos,
        "registros_limpios": registros_limpios,
        "raw_backup": str(raw_csv_path),
        "cleaned_backup": str(clean_csv_path) if registros_limpios > 0 else None,
    }

    (BACKUPS_DIR / f"etl_log_{ts}.json").write_text(
        json.dumps(log_data, indent=4), encoding="utf-8"
    )

    print("✅ ETL finalizado correctamente.")
    return log_data
