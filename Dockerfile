# Dockerfile - Empaquetado del Motor de Análisis (Micro-SPS 02)
# Arquitectura: Contenedor Inmutable

# 1. Base Image (Fijamos una versión específica por seguridad)
FROM python:3.10-slim-bookworm

# 2. Dependencias del Sistema (OS Layer)
# Aquí instalamos ffmpeg, crucial para Whisper/Librosa
RUN apt-get update && apt-get install -y --no-install-recommends     ffmpeg     && rm -rf /var/lib/apt/lists/*

# 3. Usuario No-Root (Seguridad en Contenedores)
RUN useradd -m appuser
WORKDIR /app

# 4. Dependencias de la Aplicación (Python Layer)
# En un proyecto real copiaríamos requirements.txt o pyproject.toml
RUN pip install --no-cache-dir openai-whisper librosa torch numpy

# 5. Código Fuente
COPY src/ /app/src/

# 6. Ejecución como usuario seguro
USER appuser

# Entrypoint por defecto (CLI)
ENTRYPOINT ["python", "-m", "english_editor.modules.analysis.presentation.cli"]
