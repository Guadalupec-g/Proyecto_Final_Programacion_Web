# Dockerfile
FROM python:3.12-slim

# Evita buffering y crea carpeta
ENV PYTHONUNBUFFERED=1
WORKDIR /app/InfoMundi

# Instala dependencias
COPY InfoMundi/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copia código
COPY InfoMundi /app/InfoMundi

# Puerto del backend
EXPOSE 8000

# Arranca FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
