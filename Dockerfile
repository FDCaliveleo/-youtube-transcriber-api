# Usamos una imagen oficial de Python como base
FROM python:3.9-slim-buster

# Establecemos el directorio de trabajo en el contenedor
WORKDIR /app

# Actualizamos e instalamos las dependencias del sistema
# Incluimos build-essential (para gcc), portaudio19-dev (para PyAudio),
# python3-dev (para cabeceras de Python), pkg-config, ffmpeg y libffi-dev
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    portaudio19-dev \
    python3-dev \
    pkg-config \
    ffmpeg \
    libffi-dev

# Copiamos el archivo de requerimientos
COPY requirements.txt .

# Instalamos las dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el resto del código de la aplicación
COPY . .

# Comando para ejecutar la aplicación usando Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]