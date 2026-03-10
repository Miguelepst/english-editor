
# Dockerfile - Empaquetado del Motor de Análisis (Micro-SPS 02)
# Arquitectura: Contenedor Inmutable Dinámico (Estándar PyPA)

ARG PYTHON_BASE=python:3.12-slim
FROM ${PYTHON_BASE}

ARG APT_REQUIREMENTS=""
RUN apt-get update && apt-get install -y --no-install-recommends \
    ${APT_REQUIREMENTS} \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m appuser
WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# 1. Capa de dependencias de terceros (Caché optimizado)
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Capa de tu aplicación (Estructura src-layout)
COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser pyproject.toml .

# 3. Instalación de tu paquete guiada por Shift-Left Audit
ARG INSTALL_CMD="pip install --no-cache-dir --no-deps ."
RUN ${INSTALL_CMD}

USER appuser

# Entrypoint limpio, Python ya sabe dónde está tu código gracias a la instalación
ENTRYPOINT ["python", "-m", "english_editor.modules.analysis.presentation.cli"]
