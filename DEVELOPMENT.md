# 🛠️ Guía de Desarrollo - English Editor

## 📋 Requisitos

- Python 3.10+
- pip

## 🚀 Instalación Rápida

```bash
# Instalar dependencias de desarrollo
make install

# O instalar manualmente
pip install -e ".[dev]"
```

## ✅ Validar Calidad del Código

```bash
# Ejecutar todas las validaciones
make verify

# Validaciones individuales
make format    # Black (formato)
make lint      # Ruff + Mypy
make test      # Pytest (tests rápidos)
make test-all  # Pytest (toda la suite)
```

## 📁 Estructura del Proyecto

```text
english-editor/
├── src/english_editor/     # Código fuente
│   ├── modules/
│   │   ├── analysis/       # Análisis de audio
│   │   └── orchestration/  # Orquestación
├── tests/
│   ├── modules/            # Tests unitarios
│   ├── e2e/                # Tests de integración
│   └── performance/        # Benchmarks
├── .github/workflows/      # CI/CD
├── Makefile                # Comandos de desarrollo
├── pyproject.toml          # Configuración del proyecto
├── ruff.toml               # Configuración de linting
├── mypy.ini                # Configuración de tipos
└── .pre-commit-config.yaml # Hooks pre-commit
```

## 🧪 Ejecutar Tests

```bash
# Tests rápidos (dominio + aplicación)
make test

# Toda la suite (incluye e2e y performance)
make test-all

# Tests con cobertura
pytest --cov=src tests/
```

## 🔧 Dependencias Opcionales

Algunos módulos requieren dependencias pesadas (Whisper, Torch, Librosa).
Los tests de integración se saltan automáticamente si no están instaladas.

```bash
# Instalar dependencias completas (incluye Whisper)
pip install -e ".[dev,whisper]"
```

## 📊 Herramientas de Calidad

| Herramienta | Propósito | Comando |
|-------------|-----------|---------|
| Black | Formato de código | `make format` |
| Ruff | Linting rápido | `ruff check src/` |
| Mypy | Verificación de tipos | `make lint` |
| Pytest | Tests unitarios | `make test` |

## 🚨 Solución de Problemas

### Mypy reporta errores en imports opcionales

Esto es esperado para dependencias como `whisper`, `torch`, `librosa`.
El archivo `mypy.ini` ya configura excepciones para estos casos.

### Ruff reporta F401 (imports no usados) en tests

Esto es intencional para verificar disponibilidad de dependencias.
El archivo `ruff.toml` ignora F401 en archivos de test.

## 📚 Recursos

- [Python Packaging Guide](https://packaging.python.org/)
- [PEP 621 - pyproject.toml](https://peps.python.org/pep-0621/)
- [Pre-Commit Hooks](https://pre-commit.com/)
