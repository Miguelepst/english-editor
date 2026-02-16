
# Modular Monolith Scaffold — Vertical Slice Architecture

Plantilla base para proyectos Python con arquitectura limpia orientada a crecimiento controlado.

## ✨ Filosofía del scaffold

- **Vertical Slice Architecture**: Cada bounded context contiene sus propias capas (domain/, application/, infrastructure/)
- **Core universal**: core/ contiene SOLO building blocks reusables en CUALQUIER dominio (Value Objects matemáticos/lógicos)
- **Módulos explícitos**: modules/ está vacío inicialmente — los bounded contexts emergen del dominio mediante add_module.py
- **Zero business logic**: Este scaffold NO contiene lógica de negocio específica — es una plantilla reusable

## 🚀 Primeros pasos

### 1. Instalación editable (requerida para imports fuera de pytest)
```bash
cd <nombre_proyecto> && pip install -e ".[dev]"
```

✅ Esto registra tu paquete en el entorno Python, permitiendo imports limpios:
```python
from <package_name>.core.value_objects import PositiveValue  # ✅ Funciona sin sys.path hacks
```

💡 **Nota importante**:
- `pytest` funciona sin este paso (lee `pythonpath = ["src"]` automáticamente)
- Scripts ejecutables, notebooks y demos **requieren** `pip install -e .`

### 2. Validar configuración
```bash
python -m pytest -v  # Tests + cobertura integrada
```

### 3. Agregar tu primer bounded context
```bash
python /content/add_module.py <nombre_proyecto> <nombre_modulo>
```

Ejemplo:
```bash
python /content/add_module.py english_editor processing
```


## 📦 Nomenclatura: Repo vs. Paquete Python

| Concepto | Formato | Ejemplo | ¿Dónde se usa? |
|----------|---------|---------|----------------|
| **Nombre del repositorio** | kebab-case | `english-editor` | URL de GitHub, carpeta raíz del proyecto |
| **Nombre del paquete Python** | snake_case | `english_editor` | Imports: `from english_editor.core...` |

💡 **Regla mnemotécnica**:
> *"Guiones **medios** para el **medio** (GitHub), guiones **bajos** para el **código** (Python)"*

✅ **Ejemplo de uso correcto**:
```python
# ✅ Correcto: snake_case en imports
from english_editor.core.value_objects import PositiveValue

# ❌ Incorrecto: kebab-case en imports → SyntaxError
# from english-editor.core...  → Python interpreta "-" como resta



## 🔁 Recarga limpia en Google Colab (sin reiniciar kernel)

En entornos efímeros como Google Colab, los imports pueden quedar en caché tras
cambios estructurales, causando errores como:

```
ModuleNotFoundError: No module named '<package_name>.modules'
```

### Solución profesional (APIs oficiales de Python):
```python
# Tras crear un nuevo módulo o reinstalar el paquete
!python reload.py <nombre_proyecto>
```

✅ Mecanismo:
- `site.main()` → Recarga paths de site-packages
- `importlib.invalidate_caches()` → Invalida cachés internas
- Limpieza selectiva de `sys.modules` → Solo afecta tu proyecto

💡 **Flujo recomendado en Colab**:
```python
# 1. Crear módulo
!python /content/add_module.py english_editor processing

# 2. Recargar para que Python lo reconozca
!python /content/english_editor/reload.py english_editor

# 3. ¡Ahora sí puedes importar!
from english_editor.modules.processing.domain.entities import ExampleEntity
```

## 🛠️ Herramientas de calidad integradas

El scaffold incluye configuración profesional para:

| Herramienta | Comando | Propósito |
|-------------|---------|-----------|
| **pytest** | `pytest` | Testing con cobertura HTML (`htmlcov/`) |
| **ruff** | `ruff check . --fix` | Linting + formateo moderno (100x más rápido que flake8+black) |
| **mypy** | `mypy src/` | Type checking estricto desde el inicio |
| **pytest-cov** | `pytest --cov` | Cobertura mínima 80% (falla si no se cumple) |

Todas están declaradas en `pyproject.toml` → el usuario decide cuándo instalarlas:
```bash
pip install -e ".[dev]"  # Instala todas las herramientas de desarrollo
```

## 📂 Estructura

Ver `ARCHITECTURE.yaml` para el mapa arquitectónico completo.

## 📜 Licencia

MIT — libre para usar en proyectos comerciales y open source.
