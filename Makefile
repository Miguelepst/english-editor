# Makefile - Contrato de Calidad Local
.PHONY: install format lint test test-all verify clean

install:
	@echo "📦 Instalando dependencias de desarrollo..."
	pip install pytest pytest-cov black ruff mypy psutil

format:
	@echo "🎨 Formateando código con Black..."
	black src/ tests/

lint:
	@echo "🔍 Ejecutando análisis estático (Ruff & Mypy)..."
	ruff check src/ tests/
	mypy src/ --ignore-missing-imports

test:
	@echo "🧪 Ejecutando Tests Unitarios (Rápidos)..."
	pytest tests/modules/analysis/domain tests/modules/analysis/application -v

test-all:
	@echo "🚀 Ejecutando TODA la suite (Incluyendo Integración/E2E)..."
	pytest tests/ -v

verify: format lint test
	@echo "✅ VALIDACIÓN EXITOSA: El código cumple el Contrato de Calidad."

clean:
	@echo "🧹 Limpiando caché y archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
