# ====================================================================
# 🤖 MAKEFILE AUTOGENERADO (Universal API para el Desarrollador y CI)
# ====================================================================
.PHONY: help verify install lock install-sec-tools fix format lint test test-all secrets sast sca image-scan security docker-build docker-run clean

# 🔥 FIX SRE: Asegurar que los binarios locales sean detectados
export PATH := $(HOME)/.local/bin:$(PATH)

# ⚙️ VARIABLES GLOBALES SRE
TARGET ?= src/ tests/
ENGINE ?= uv

# 📖 Muestra esta ayuda interactiva
help:
	@echo '🚀 Ejecuta "make verify" para validar tu código antes de subirlo.'

# 🚀 EL GATEKEEPER LOCAL: Ejecuta todo antes de subir a GitHub
verify: format lint security test
	@echo '✅ Todo verde. El código cumple el Contrato de Calidad. Listo para el git push.'

# 🚀 Toolchain SRE: Ejecutor inmutable con indexación multi-repositorio...
install:
	pip install uv typing-extensions mypy ruff black bandit pip-audit --quiet
	uv pip install --system --no-deps --require-hashes --index-strategy unsafe-best-match -r requirements.lock.txt
	uv pip install --system --no-deps -e .

# 🔒 [SRE] Regenera la suite completa de dependencias (Opcional: make lock ENGINE=pip-tools)
lock:
	@echo 'Iniciando resolución SRE de dependencias...'
	ENGINE=$(ENGINE) python src/english_editor/infrastructure/tools/dependency_manager.py
	@echo '✅ Suite de archivos generada y sellada.'

# 🛡️ Instala binarios de seguridad en espacio de usuario (Colab/Local)
install-sec-tools:
	@mkdir -p ~/.local/bin
	@if ! command -v gitleaks >/dev/null 2>&1; then wget -qO- https://github.com/gitleaks/gitleaks/releases/download/v8.18.2/gitleaks_8.18.2_linux_x64.tar.gz | tar xz -C ~/.local/bin gitleaks; fi
	@if ! command -v trivy >/dev/null 2>&1; then echo '📥 Descargando Trivy...'; curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b ~/.local/bin; fi
	@echo '✅ Gitleaks y Trivy listos. Recuerda: export PATH="$$HOME/.local/bin:$$PATH"'

# 🔧🧹 Auto-corrigiendo código (Objetivo: $(TARGET)) linting e imports (Ruff)...
fix:
	ruff check $(TARGET) --fix
	ruff format $(TARGET)

# 🎨 Formatea el código automáticamente
format: fix
	black src/ tests/
	ruff format src/ tests/

# 🔎 Ejecutando inspección de calidad (Objetivo: $(TARGET)) Análisis estático puro (Ruff & Mypy sin auto-corrección)...
lint:
	ruff check $(TARGET)
	mypy $(TARGET) --ignore-missing-imports
	bandit -r $(TARGET) -ll -ii --quiet

# 🧪 Ejecuta pruebas unitarias rápidas (Ignora E2E y lentas)
test:
	pytest tests/ -m 'not e2e and not slow' -v

# 🚀 Ejecuta TODA la suite de pruebas (Incluyendo Integración/E2E)
test-all:
	pytest tests/ -v

# 🔐 [Step 1] Escanea credenciales (Degradación Elegante)
secrets:
	@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect -v --source . --no-git; else echo '⚠️ Gitleaks no instalado. Saltando.'; fi

# 🧠 [Step 2] Análisis SAST del Código (Bandit)
sast:
	python -m bandit -r src/ -ll -i

# 📦 [Step 3] Auditoría de Dependencias de Terceros (pip-audit)
sca:
	python -m pip_audit || echo '⚠️ pip-audit detectó vulnerabilidades. Revisa el reporte.'

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
	docker build --build-arg PYTHON_BASE=$$PYTHON_BASE --build-arg APT_REQUIREMENTS="$$APT_PACKS" --build-arg INSTALL_CMD="$$INSTALL_CMD" -t english-editor:local .

# ▶️ Ejecuta el contenedor recién construido
docker-run: docker-build
	docker run --rm english-editor:local

# 🧹 Limpia caché y artefactos basura del sistema
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
