# Usamos una imagen oficial de Python como base
FROM python:3.9-slim-bullseye

# Establecemos el directorio de trabajo en el contenedor
WORKDIR /app

# Actualizamos e instalamos las dependencias del sistema
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends build-essential portaudio19-dev python3-dev pkg-config ffmpeg libffi-dev && rm -rf /var/lib/apt/lists/*

# Copiamos el archivo de requerimientos
COPY requirements.txt .

# Actualizamos pip y luego instalamos las dependencias de Python
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de la aplicación
COPY . .

# Comando para ejecutar la aplicación usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]