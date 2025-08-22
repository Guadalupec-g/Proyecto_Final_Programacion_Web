# 📄 README.md — Proyecto InfoMundi 🌍

## 📌 Descripción
**InfoMundi** es un proyecto académico que combina un **frontend web**, un **backend con FastAPI**, una **base de datos MySQL** y un **pipeline ETL automatizado**.  

El sistema permite:  
- Buscar países y guardar favoritos.  
- Almacenar datos en una tabla RAW.  
- Procesarlos mediante un **ETL (Extract, Transform, Load)** que limpia, valida y normaliza.  
- Guardar resultados en una tabla CLEANED.  
- Generar **backups (CSV + log JSON)** automáticamente.  
- Mostrar los datos limpios en el frontend.  

---

## 🛠️ Tecnologías usadas
- **Frontend**: HTML, CSS, JavaScript (REST API fetch)  
- **Backend**: FastAPI (Python)  
- **ORM**: SQLAlchemy  
- **Base de datos**: MySQL  
- **ETL**: Pandas + APScheduler (para automatización)  

---

## 📂 Estructura del proyecto
```
info-mundi-main/
├── backend/
│   ├── database.py          # Configuración de conexión a MySQL
│   ├── models.py            # Modelo Favorito
│   ├── main.py              # FastAPI + Endpoints + Scheduler
│   └── etl_pipeline.py      # Script ETL
├── frontend/
│   ├── index.html           # Interfaz web
│   ├── script.js            # Lógica JS
│   └── styles.css           # Estilos
├── backups/                 # Carpeta donde se guardan CSV y logs
├── requirements.txt
└── README.md
```

---

## ⚙️ Instalación

### 1. Clonar repositorio
```bash
git clone https://github.com/DAAO1/InfoMundi.git
cd InfoMundi
```

### 2. Crear entorno virtual
```bash
python -m venv venv
```

### 3. Activar entorno virtual
- Windows:
  ```bash
  venv\Scripts\activate
  ```
- Mac/Linux:
  ```bash
  source venv/bin/activate
  ```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```
Si no tienes `requirements.txt`, instala manualmente:
```bash
pip install fastapi uvicorn sqlalchemy pymysql pandas apscheduler
```

---

## 🗄️ Base de datos MySQL

Ejecuta este script en MySQL Workbench o consola:

```sql
CREATE DATABASE IF NOT EXISTS infomundi;
USE infomundi;

CREATE TABLE IF NOT EXISTS favoritos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    comentario TEXT,
    imagen_url TEXT
);

CREATE TABLE IF NOT EXISTS raw_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100),
    pais VARCHAR(100),
    fecha DATE,
    valor FLOAT,
    fuente VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS cleaned_data (
    id INT PRIMARY KEY,
    nombre VARCHAR(100),
    pais VARCHAR(100),
    fecha DATE,
    valor FLOAT,
    fuente VARCHAR(255)
);
```

---

## ▶️ Ejecución

1. Inicia el servidor backend desde la carpeta raíz:
```bash
uvicorn backend.main:app --reload
```

2. Abre la API en tu navegador:
```
http://127.0.0.1:8000/docs
```

3. Abre el **frontend** con Live Server (o doble clic en `index.html`).

---

## 🌐 Endpoints principales

| Método | Endpoint             | Descripción |
|--------|----------------------|-------------|
| GET    | `/favoritos`         | Listar favoritos |
| POST   | `/favoritos`         | Crear un favorito |
| POST   | `/api/pipeline/run`  | Ejecutar manualmente el ETL |
| GET    | `/api/cleaned_data`  | Listar datos limpios (CLEANED) |

---

## ⏱️ ETL automático
El pipeline ETL se ejecuta automáticamente cada **5 minutos** gracias a **APScheduler**.  
- También se puede ejecutar manualmente con `/api/pipeline/run`.  
- Cada ejecución genera:  
  - `raw_backup_TIMESTAMP.csv`  
  - `cleaned_backup_TIMESTAMP.csv`  
  - `etl_log_TIMESTAMP.json`  

Todos se guardan en la carpeta `backups/`.

---

## 🖥️ Frontend
El **frontend (`index.html`)** permite:  
- Buscar países con la API de RestCountries.  
- Guardar favoritos (se almacenan en MySQL).  
- Ver la lista de favoritos guardados.  
- Ver los **datos limpios** procesados por el ETL en una tabla.

---

## 📋 Evidencias para la entrega
- Swagger con endpoints funcionando.  
- Carpeta `backups/` con CSV y logs.  
- Frontend mostrando favoritos y datos limpios.  
- Ejemplo de ejecución automática (logs con timestamps diferentes).  

---

