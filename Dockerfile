
# Dockerfile - Empaquetado del Motor de Análisis (Micro-SPS 02)
# Arquitectura: Contenedor Inmutable Dinámico

# 1. Base Image (Inyectada dinámicamente desde ci-metadata.json)
ARG PYTHON_BASE=python:3.12-slim
FROM ${PYTHON_BASE}

# 2. Dependencias del Sistema (OS Layer - Inyectadas dinámicamente)
ARG APT_REQUIREMENTS=""
RUN apt-get update && apt-get install -y --no-install-recommends \
    ${APT_REQUIREMENTS} \
    && rm -rf /var/lib/apt/lists/*

# 3. Usuario No-Root (Seguridad en Contenedores)
RUN useradd -m appuser
WORKDIR /app

# 4. Actualización de herramientas base de compilación
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 5. Dependencias de la Aplicación (Python Layer determinista)
# Copiamos el archivo generado por la herramienta OOP y le damos propiedad al usuario
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Código Fuente
# Copiamos todo tu código respetando la estructura (src/, etc.)
COPY --chown=appuser:appuser . .

# 7. Ejecución como usuario seguro
USER appuser

# Entrypoint por defecto de tu CLI real
ENTRYPOINT ["python", "-m", "english_editor.modules.analysis.presentation.cli"]
