-- Crear base de datos
CREATE DATABASE IF NOT EXISTS infomundi CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Seleccionar base de datos
USE infomundiF;

-- Tabla 1: Favoritos (parte original del proyecto InfoMundi)
CREATE TABLE IF NOT EXISTS favorito (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    comentario TEXT,
    imagen_url TEXT
);

-- Tabla 2: RAW (almacena datos en bruto)
CREATE TABLE IF NOT EXISTS raw_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    pais VARCHAR(100) NOT NULL,
    fecha DATE,
    valor FLOAT,
    fuente VARCHAR(255)
);

-- Tabla 3: CLEANED (almacena datos procesados por ETL)
CREATE TABLE IF NOT EXISTS cleaned_data (
    id INT PRIMARY KEY,
    nombre VARCHAR(100),
    pais VARCHAR(100),
    fecha DATE,
    valor FLOAT,
    fuente VARCHAR(255)
);
