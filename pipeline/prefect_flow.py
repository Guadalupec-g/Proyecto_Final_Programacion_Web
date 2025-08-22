# pipeline/prefect_flow.py
from prefect import flow, task
import os, sys

# añade InfoMundi al sys.path
ROOT = os.path.dirname(os.path.dirname(__file__))             # .../proyecto_final_programacion_web
INFOMUNDI = os.path.join(ROOT, "InfoMundi")
if INFOMUNDI not in sys.path:
    sys.path.append(INFOMUNDI)

@task(log_prints=True)
def run_etl_task():
    from backend.etl_pipeline import run_etl
    return run_etl()

@flow(log_prints=True, name="infomundi-etl")
def etl_flow():
    return run_etl_task()

if __name__ == "__main__":
    etl_flow()
