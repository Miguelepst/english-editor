# Makefile - Contrato de Calidad Local
.PHONY: install format lint test test-all verify clean fix

install:
	@echo "📦 Instalando dependencias de desarrollo..."
	pip install pytest pytest-cov black ruff mypy psutil

format:
	@echo "🎨 Formateando código con Black..."
	python -m black src/ tests/

fix:
	@echo "🔧 Auto-corrigiendo errores con Ruff..."
	python -m ruff check src/ tests/ --fix

lint:
	@echo "🔍 Ejecutando análisis estático (Ruff & Mypy)..."
	python -m ruff check src/ tests/
	python -m mypy src/ --ignore-missing-imports

test:
	@echo "🧪 Ejecutando Tests Unitarios (Rápidos)..."
	python -m pytest tests/modules/analysis/domain tests/modules/analysis/application -v

test-all:
	@echo "🚀 Ejecutando TODA la suite (Incluyendo Integración/E2E)..."
	python -m pytest tests/ -v

verify: format fix lint test
	@echo "✅ VALIDACIÓN EXITOSA: El código cumple el Contrato de Calidad."

clean:
	@echo "🧹 Limpiando caché y archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
