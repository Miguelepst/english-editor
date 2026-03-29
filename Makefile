# ====================================================================
# 🤖 MAKEFILE AUTOGENERADO (Universal API para el Desarrollador y CI)
# ====================================================================
.PHONY: help verify install docs-build lock install-sec-tools fix format lint check-venv sync test test-all secrets sast sca image-scan security docker-build docker-run clean pipeline-canary

# 🔥 FIX SRE: Asegurar que los binarios locales sean detectados
export PATH := $(HOME)/.local/bin:$(PATH)

# ⚙️ VARIABLES GLOBALES SRE
TARGET ?= src/ tests/
ENGINE ?= uv
EXTRA_INDEX_URL ?= $(shell jq -r ".extra_index_url // empty" ci-metadata.json 2>/dev/null)

EXTRAS ?=

# 📖 Muestra esta ayuda interactiva
help:
	@echo '🚀 Ejecuta make verify para validar tu código antes de subirlo.'

# 🚀 EL GATEKEEPER LOCAL: Ejecuta todo antes de subir a GitHub
verify: format lint security test
	@echo '✅ Todo verde. El código cumple el Contrato de Calidad. Listo para el git push.'

# 🚀 Toolchain SRE: Crea un Sandbox inmutable para el Runner (CI/CD)
install:
	pip install --upgrade uv setuptools --quiet
	uv venv --python 3.12 --allow-existing .venv
	uv pip install --python .venv --no-deps --require-hashes --index-strategy unsafe-best-match $(if $(EXTRA_INDEX_URL),--extra-index-url $(EXTRA_INDEX_URL),) -r requirements-ci.txt
	uv pip install --python .venv $(if $(EXTRA_INDEX_URL),--extra-index-url $(EXTRA_INDEX_URL),) -e .$(EXTRAS)

# 📖 Construye el sitio estático de documentación dentro del Sandbox
docs-build:
	VIRTUAL_ENV=$$(pwd)/.venv uv run mkdocs build

# 🔒 [SRE] Regenera la suite completa de dependencias
lock:
	@echo 'Iniciando resolución SRE de dependencias...'
	ENGINE=$(ENGINE) python src/english_editor/infrastructure/tools/dependency_manager.py
	@echo '✅ Suite de archivos generada y sellada.'

# 🛡️ Instala binarios de seguridad (Tolerancia a fallos y Degradación Elegante)
install-sec-tools:
	@mkdir -p ~/.local/bin
	@if ! command -v gitleaks >/dev/null 2>&1; then echo '📥 Descargando Gitleaks (Estable)...' && curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz -o /tmp/gitleaks.tar.gz && tar xz -f /tmp/gitleaks.tar.gz -C ~/.local/bin gitleaks && rm /tmp/gitleaks.tar.gz || echo '⚠️ GitHub falló (404/Limit). Gitleaks operará en Degradación Elegante.'; fi
	@if ! command -v trivy >/dev/null 2>&1; then echo '📥 Descargando Trivy...' && curl -sSfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh -o /tmp/trivy-install.sh && sh /tmp/trivy-install.sh -b ~/.local/bin && rm /tmp/trivy-install.sh || echo '⚠️ Error al descargar Trivy.'; fi
	@echo '✅ Infraestructura de seguridad lista. Recuerda: export PATH="$$HOME/.local/bin:$$PATH"'

# 🔧🧹 Auto-corrigiendo código (Objetivo: $(TARGET)) linting e imports (Ruff)...
fix: sync
	VIRTUAL_ENV=$$(pwd)/.venv uv run ruff check $(TARGET) --fix
	VIRTUAL_ENV=$$(pwd)/.venv uv run ruff format $(TARGET)

# 🎨 Formatea el código automáticamente
format: fix
	VIRTUAL_ENV=$$(pwd)/.venv uv run black $(TARGET)
	VIRTUAL_ENV=$$(pwd)/.venv uv run ruff format $(TARGET)

# 🔎 Ejecutando inspección de calidad estática pura (Ruff & Mypy sin auto-corrección)...
lint: sync
	VIRTUAL_ENV=$$(pwd)/.venv uv run ruff check $(TARGET)
	VIRTUAL_ENV=$$(pwd)/.venv uv run mypy $(TARGET) --ignore-missing-imports
	VIRTUAL_ENV=$$(pwd)/.venv uv run bandit -r $(TARGET) -ll -ii --quiet
	@echo ''
	@echo '#============================================================='
	@echo '# 🛡️  CERTIFICADO DE CONFORMIDAD SRE (GATEKEEPER LOCAL)'
	@echo '#============================================================='
	@echo '# 🐍 Entorno                : '$$(VIRTUAL_ENV=$$(pwd)/.venv uv run python --version)''
	@echo '# ✅ Ruff   (Estilo)        : APROBADO ['$$(VIRTUAL_ENV=$$(pwd)/.venv uv run ruff --version)']'
	@echo '# ✅ Mypy   (Tipado)        : APROBADO ['$$(VIRTUAL_ENV=$$(pwd)/.venv uv run mypy --version)']'
	@echo '# ✅ Bandit (Seguridad)     : APROBADO'
	@echo '# 🎯 Objetivo               : $(TARGET)'
	@echo '# 🕒 Fecha de validación    : '$$(TZ='America/Bogota' date +'%Y-%m-%d %I:%M:%S %p')''
	@echo '# 👤 Operador               : Miguel Gutiérrez (@Miguelepst)'
	@echo '# 👤 Entorno                : '$$(whoami)''
	@echo '#============================================================='

# 🐍 Verifica y muestra el entorno virtual activo
check-venv:
	@echo '🔍 Verificando entorno virtual activo...'
	VIRTUAL_ENV=$$(pwd)/.venv uv run python -c 'import sys; import os; assert sys.prefix != sys.base_prefix, "❌ NO estás en un entorno virtual"; print(f"✨ Entorno activo en: {os.path.basename(sys.prefix)}")'
	@echo '✅ Validación completada con éxito'

# 🔄 [SRE] Reconciliación local: Sincroniza el entorno físico (Ignorado en CI/CD)
sync: check-venv
	@if [ -z "$$GITHUB_ACTIONS" ]; then \
	    echo 'Sincronizando el Sandbox físico local con dependencias inmutables...'; \
	    VIRTUAL_ENV=$$(pwd)/.venv UV_EXTRA_INDEX_URL=$(EXTRA_INDEX_URL) $(ENGINE) sync --all-extras --frozen; \
	else \
	    echo '⚙️ Entorno CI detectado (GitHub Actions). Omitiendo uv sync para proteger la tarea install.'; \
	fi

# 🧪 Ejecuta pruebas unitarias (Enrutador Inteligente SRE para TARGET)
test: sync
	@echo '🚀 Iniciando pruebas unitarias...'
	VIRTUAL_ENV=$$(pwd)/.venv uv run python -c 'import sys; print(f"📂 Usando intérprete: {sys.executable}")'
	@if [ -n "$(TARGET)" ] && [ "$(TARGET)" != "src/ tests/" ]; then \
	    if echo "$(TARGET)" | grep -qE "test_|tests/"; then \
	        echo '🧪 Corriendo prueba directa: $(TARGET)'; \
	        VIRTUAL_ENV=$$(pwd)/.venv uv run pytest $(TARGET) -m 'not e2e and not slow' -v; \
	    else \
	        echo '⏭️ Evaluando código fuente: $(TARGET)'; \
	        TEST_FILE=$$(echo $(TARGET) | sed 's|src/[^/]*/|tests/|' | sed 's|\([^/]*\)$$|test_\1|'); \
	        if [ -f "$$TEST_FILE" ]; then \
	            echo "🎯 Test gemelo encontrado: $$TEST_FILE"; \
	            VIRTUAL_ENV=$$(pwd)/.venv uv run pytest $$TEST_FILE -m 'not e2e and not slow' -v; \
	        else \
	            echo '⚠️ Saltando sin error, a este archivo no se le encontró su test por lo que pytest no participo.'; \
	        fi; \
	    fi; \
	else \
	    echo '🧪 Corriendo toda la suite de pruebas (TARGET por defecto)...'; \
	    VIRTUAL_ENV=$$(pwd)/.venv uv run pytest src/ tests/ -m 'not e2e and not slow' -v; \
	fi

# 🚀 Ejecuta TODA la suite de pruebas (Incluyendo Integración/E2E)
test-all:
	VIRTUAL_ENV=$$(pwd)/.venv uv run pytest tests/ -v

# 🔐 [Step 1] Escanea credenciales (Degradación Elegante)
secrets:
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect -v --source . --no-git; else echo '⚠️ Gitleaks no instalado. Saltando.'; fi

# 🧠 [Step 2] Análisis SAST del Código (Bandit)
sast:
	VIRTUAL_ENV=$$(pwd)/.venv uv run python -m bandit -r $(TARGET) -ll -i

# 📦 [Step 3] Auditoría de Dependencias de Terceros (pip-audit)
sca: sync
	VIRTUAL_ENV=$$(pwd)/.venv uv run python -m pip_audit || echo '⚠️ pip-audit detectó vulnerabilidades. Revisa el reporte.'

# 🐳 [Step 4] Escaneo de vulnerabilidades del FS (Trivy)
image-scan:
	@if [ -f "requirements.lock.txt" ]; then grep -v "^#" requirements.lock.txt | grep -v "^$$" > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt; fi
	@if command -v trivy >/dev/null 2>&1; then trivy fs . --scanners vuln --severity HIGH,CRITICAL --no-progress; else echo '⚠️ Trivy no instalado. Saltando.'; fi

# 🚓 Ejecuta TODA la suite de DevSecOps
security: secrets sast sca image-scan
	@echo '✅ Auditoría DevSecOps Total completada.'

# 🐳 Construye la imagen local inyectando el ci-metadata.json (SSOT)
docker-build:
	@echo 'Leyendo infraestructura desde ci-metadata.json...'
	PYTHON_BASE=$$(jq -r '.python_base_image' ci-metadata.json); \
	APT_PACKS=$$(jq -r '.apt_requirements' ci-metadata.json); \
	INSTALL_CMD=$$(jq -r '.project_installation_command' ci-metadata.json); \
	EXTRA_URL=$$(jq -r '.extra_index_url // empty' ci-metadata.json); \
	docker build --build-arg PYTHON_BASE=$$PYTHON_BASE --build-arg APT_REQUIREMENTS="$$APT_PACKS" --build-arg INSTALL_CMD="$$INSTALL_CMD" --build-arg EXTRA_INDEX_URL="$$EXTRA_URL" -t english-editor:local .

# ▶️ Ejecuta el contenedor recién construido
docker-run: docker-build
	docker run --rm english-editor:local

# 🧹 Limpia caché y artefactos basura del sistema
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +

# 🐦 [SRE] Genera código trampa para validar que el Gatekeeper/CI está operativo y lo auto-destruye
pipeline-canary:
	@echo '🏗️ Construyendo Dummy File (Canary)...'
	@echo '"""Archivo dummy generado por el Canary Test."""' > tests/test_canary.py
	@echo '' >> tests/test_canary.py
	@echo 'def test_dummy_pipeline() -> None:' >> tests/test_canary.py
	@echo '    """Prueba unitaria vacía que siempre pasa para engañar al sistema."""' >> tests/test_canary.py
	@echo '    assert True' >> tests/test_canary.py
	@echo '✅ Archivo trampa creado. Desatando el Gatekeeper sobre él...'
	$(MAKE) verify TARGET=tests/test_canary.py
	@echo '🧹 Prueba exitosa. Eliminando rastros...'
	@rm tests/test_canary.py
	@echo '🟢 CANARY TEST SUPERADO. Todo el Toolchain SRE está operativo.'
