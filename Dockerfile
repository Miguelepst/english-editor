# ==============================================================================
# 🐳 DOCKERFILE UNIVERSAL DEVSECOPS (Plantilla Base Empresarial)
# Propósito: Empaquetar aplicaciones Python bajo estándares SRE y PyPA.
# ==============================================================================

ARG PYTHON_BASE=python:3.12-slim
FROM ${PYTHON_BASE}

# [ASPECTO CRÍTICO 2]: Zona Horaria (Timezone)
ENV TZ="America/Bogota"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ARG APT_REQUIREMENTS=""
ARG EXTRA_INDEX_URL=""
RUN apt-get update && apt-get install -y --no-install-recommends \
    ${APT_REQUIREMENTS} \
    && rm -rf /var/lib/apt/lists/*

# Creamos un usuario no-root por seguridad
RUN useradd -m appuser
WORKDIR /app

# [ASPECTO CRÍTICO 1]: Permisos de Escritura en Volúmenes
RUN mkdir -p /app/data /home/appuser/.cache \
    && chown -R appuser:appuser /app /home/appuser

RUN pip install --no-cache-dir --upgrade pip setuptools wheel



# Capas de dependencias y código (Caché optimizado)
COPY --chown=appuser:appuser requirements.txt .

# 🧠 INYECCIÓN SRE: Instalación dinámica basada en la fuente de verdad
RUN if [ -z "$EXTRA_INDEX_URL" ]; then \
      pip install --no-cache-dir --no-deps --require-hashes -r requirements.txt; \
    else \
      pip install --no-cache-dir --no-deps --require-hashes --extra-index-url "$EXTRA_INDEX_URL" -r requirements.txt; \
    fi






COPY --chown=appuser:appuser src/ src/
COPY --chown=appuser:appuser pyproject.toml .

# Instalación inyectada por Shift-Left
ARG INSTALL_CMD="pip install --no-cache-dir --no-deps ."
RUN ${INSTALL_CMD}

USER appuser

# [OPCIÓN 2]: Inmortalidad Offline para Inteligencia Artificial (Descarga de modelos)
RUN python -c "import whisper; whisper.load_model('tiny.en'); whisper.load_model('base.en')"

# [ASPECTO CRÍTICO 3]: Entrypoint limpio (Formato Exec)
ENTRYPOINT ["python", "-m", "english_editor.modules.analysis.presentation.cli"]
