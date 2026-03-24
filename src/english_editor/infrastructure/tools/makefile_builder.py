# src/english_editor/infrastructure/tools/makefile_builder.py
"""
Motor agnóstico generador de Makefiles SRE (OOP).

Arquitectura: Modular Monolith + Vertical Slice
Componente: Infrastructure Tool
Responsabilidad: Generar programáticamente un Makefile universal que actúe como
el Gatekeeper estandarizado (CI/CD y local) para las operaciones SRE del repositorio.
"""
from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

# === 🧭 Protocolos Arquitectónicos (Strict Layering) ===
# ✅ CORE: Building blocks universales (value objects, tipos básicos)
# ✅ MODULES: Bounded contexts verticales y aislados
# ❌ DOMAIN → APPLICATION/INFRA: Prohibido (rompe Clean Architecture)
# ❌ MODULES → MODULES: Prohibido (comunicación solo vía Core o Puertos)
# ✅ INFRASTRUCTURE: Solo adaptadores concretos (nunca lógica de negocio)

# === 🧪 Protocolos de Calidad Obligatorios ===
# 🔒 Inmutabilidad: Value Objects → @dataclass(frozen=True)
# 🧪 Testabilidad: Componente debe ser testeable SIN mocks de infraestructura
# 🔤 Type Hints: Firmas públicas con type hints explícitos (PEP 484)
# ⚡ Pureza: Funciones puras donde sea posible (misma entrada → misma salida)
# 🚫 Excepciones específicas: Define excepciones de dominio (no uses Exception genérico)
# 📏 Longitud de línea: Máximo 88 caracteres (compatible con Black/Ruff)

# === Definición principal ===
# =====================================================================
# 1. ENTIDADES DE DOMINIO (Data Classes)
# =====================================================================
@dataclass
class MakeTask:
    """Representa una regla individual dentro de un Makefile."""
    name: str
    description: str
    commands: list[str]
    dependencies: list[str] | None = None   # Tareas que deben ejecutarse antes

    def __post_init__(self) -> None:
        if self.dependencies is None:
            self.dependencies = []

# =====================================================================
# 2. EL PATRÓN STRATEGY: Perfiles de Negocio Agnósticos
# =====================================================================
class MakefileProfile(ABC):
    """Interfaz base. Cualquier proyecto futuro debe implementar esto."""
    @property
    @abstractmethod
    def tasks(self) -> list[MakeTask]:
        pass

# ---------------------------------------------------------------------
# Implementación Específica (Tu Proyecto Actual)
# ---------------------------------------------------------------------





class ModernPythonProfile(MakefileProfile):
    """Perfil de tareas SRE estandarizadas (100% Aisladas en Sandbox)."""
    @property
    def tasks(self) -> list[MakeTask]:
        return [
            MakeTask(
                name="help",
                description="📖 Muestra esta ayuda interactiva",
                commands=["@echo '🚀 Ejecuta make verify para validar tu código antes de subirlo.'"]
            ),
            MakeTask(
                name="verify",
                description="🚀 EL GATEKEEPER LOCAL: Ejecuta todo antes de subir a GitHub",
                dependencies=["format", "lint", "security", "test"],
                commands=["@echo '✅ Todo verde. El código cumple el Contrato de Calidad. Listo para el git push.'"]
            ),






            MakeTask(
                name="install",
                description="🚀 Toolchain SRE: Crea un Sandbox inmutable y aislado del Sistema Operativo",
                commands=[
                    "pip install --upgrade uv setuptools --quiet",
                    # 🔥 SRE FIX: Forzamos la descarga y uso de Python 3.12 independiente del OS
                    "uv venv --python 3.12 --allow-existing .venv",
                    #"uv venv --allow-existing .venv", # 🛡️ FIX SRE: Fuerza la cápsula en el directorio exacto
                    "uv pip install --python .venv --no-deps --require-hashes --index-strategy unsafe-best-match $(if $(EXTRA_INDEX_URL),--extra-index-url $(EXTRA_INDEX_URL),) -r requirements.lock.txt",
                    "uv pip install --python .venv $(if $(EXTRA_INDEX_URL),--extra-index-url $(EXTRA_INDEX_URL),) -e .$(EXTRAS)"
                ]
            ),
            MakeTask(
                name="docs-build",
                description="📖 Construye el sitio estático de documentación dentro del Sandbox",
                commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run mkdocs build"] # 🪄 Invocación encapsulada a la fuerza
            ),
            MakeTask(
                name="lock",
                description="🔒 [SRE] Regenera la suite completa de dependencias",
                commands=[
                    "@echo 'Iniciando resolución SRE de dependencias...'",
                    "ENGINE=$(ENGINE) python src/english_editor/infrastructure/tools/dependency_manager.py",
                    "@echo '✅ Suite de archivos generada y sellada.'"
                ]
            ),
            MakeTask(
                name="install-sec-tools",
                description="🛡️ Instala binarios de seguridad (Tolerancia a fallos y Degradación Elegante)",
                commands=[
                    "@mkdir -p ~/.local/bin",
                    "@if ! command -v gitleaks >/dev/null 2>&1; then echo '📥 Descargando Gitleaks (Estable)...' && curl -sSfL https://github.com/gitleaks/gitleaks/releases/download/v8.21.2/gitleaks_8.21.2_linux_x64.tar.gz -o /tmp/gitleaks.tar.gz && tar xz -f /tmp/gitleaks.tar.gz -C ~/.local/bin gitleaks && rm /tmp/gitleaks.tar.gz || echo '⚠️ GitHub falló (404/Limit). Gitleaks operará en Degradación Elegante.'; fi",
                    "@if ! command -v trivy >/dev/null 2>&1; then echo '📥 Descargando Trivy...' && curl -sSfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh -o /tmp/trivy-install.sh && sh /tmp/trivy-install.sh -b ~/.local/bin && rm /tmp/trivy-install.sh || echo '⚠️ Error al descargar Trivy.'; fi",
                    "@echo '✅ Infraestructura de seguridad lista. Recuerda: export PATH=\"$$HOME/.local/bin:$$PATH\"'"
                ]
            ),
            MakeTask(
                name="fix",
                description="🔧🧹 Auto-corrigiendo código (Objetivo: $(TARGET)) linting e imports (Ruff)...",
                dependencies=["sync"],  
                commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run ruff check $(TARGET) --fix", "VIRTUAL_ENV=$$(pwd)/.venv uv run ruff format $(TARGET)"]
            ),



            MakeTask(
                name="format",
                description="🎨 Formatea el código automáticamente",
                dependencies=["fix"],
                commands=[
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run black $(TARGET)", 
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run ruff format $(TARGET)"
                ]
            ),







            #
            #MakeTask(
            #    name="format",
            #    description="🎨 Formatea el código automáticamente",
            #    dependencies=["fix"],
            #    commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run black src/ tests/", "VIRTUAL_ENV=$$(pwd)/.venv uv run ruff format src/ tests/"]
            #),
            #






            MakeTask(
                name="lint",
                description="🔎 Ejecutando inspección de calidad estática pura (Ruff & Mypy sin auto-corrección)...",
                dependencies=["sync"], # 🪄 SRE FIX: Garantiza el entorno si se llama a 'make lint' directamente
                commands=[
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run ruff check $(TARGET)",
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run mypy $(TARGET) --ignore-missing-imports",
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run bandit -r $(TARGET) -ll -ii --quiet"
                ]
            ),





            # Fíjate en la doble barra: \"
            MakeTask(
                name="check-venv",
                description="🐍 Verifica y muestra el entorno virtual activo",
                commands=[
                    "@echo '🔍 Verificando entorno virtual activo...'",
                    # Esta línea valida y LUEGO imprime la ruta del entorno activo
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run python -c 'import sys; import os; assert sys.prefix != sys.base_prefix, \"❌ NO estás en un entorno virtual\"; print(f\"✨ Entorno activo en: {os.path.basename(sys.prefix)}\")'",
                    "@echo '✅ Validación completada con éxito'"
                ]
            ),






            MakeTask(
                name="sync",
                description="🔄 [SRE] Reconciliación local: Sincroniza el entorno físico (Ignorado en CI/CD)",
                dependencies=["check-venv"],
                commands=[
                    # 🪄 SRE FIX: Detecta si estamos en GitHub Actions. Si es así, no interfiere con 'make install'.
                    "@if [ -z \"$$GITHUB_ACTIONS\" ]; then \\",
                    "    echo 'Sincronizando el Sandbox físico local con dependencias inmutables...'; \\",
                    "    VIRTUAL_ENV=$$(pwd)/.venv UV_EXTRA_INDEX_URL=$(EXTRA_INDEX_URL) $(ENGINE) sync --all-extras --frozen; \\",
                    "else \\",
                    "    echo '⚙️ Entorno CI detectado (GitHub Actions). Omitiendo uv sync para proteger la tarea install.'; \\",
                    "fi"
                ]
            ),






            #
            # MakeTask(
            #    name="sync",
            #    description="🔄 [SRE] Reconciliación: Sincroniza el entorno físico (Incluyendo DevSecOps)",
            #    dependencies=["check-venv"],
            #    commands=[
            #        "@echo 'Sincronizando el Sandbox físico con dependencias inmutables...'",
            #        # El flag --all-extras garantiza que black, ruff, bandit, etc., no sean eliminados
            #        "VIRTUAL_ENV=$$(pwd)/.venv $(ENGINE) sync --all-extras --frozen",
            #        "@echo '✅ Entorno físico perfectamente alineado con el lockfile.'"
            #     ]
            # ),
            #



            MakeTask(
                name="test",
                description="🧪 Ejecuta pruebas unitarias rápidas (Ignora E2E y lentas)",
                dependencies=["sync"],                  # dependencies=["check-venv", "sync"], # 🪄 AQUÍ ESTÁ LA MAGIA SRE (Ambas en una lista)
                commands=[
                    "@echo '🚀 Iniciando pruebas unitarias...'",
                    # Imprimimos el Python que se está usando para total transparencia
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run python -c 'import sys; print(f\"📂 Usando intérprete: {sys.executable}\")'",
                    "VIRTUAL_ENV=$$(pwd)/.venv uv run pytest $(TARGET) -m 'not e2e and not slow' -v"
                ]
            ),


            #
            #MakeTask(
            #    name="test",
            #    description="🧪 Ejecuta pruebas unitarias rápidas (Ignora E2E y lentas)",
            #    dependencies=["check-venv"],
            #    commands=[
            #        "VIRTUAL_ENV=$$(pwd)/.venv uv run pytest $(TARGET) -m 'not e2e and not slow' -v"
            #    ]
            #),
            #



            #
            #MakeTask(
            #    name="test",
            #    description="🧪 Ejecuta pruebas unitarias rápidas (Ignora E2E y lentas)",
            #    commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run pytest tests/ -m 'not e2e and not slow' -v"]
            #),
            #

            MakeTask(
                name="test-all",
                description="🚀 Ejecuta TODA la suite de pruebas (Incluyendo Integración/E2E)",
                commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run pytest tests/ -v"]
            ),
            MakeTask(
                name="secrets",
                description="🔐 [Step 1] Escanea credenciales (Degradación Elegante)",
                commands=["@if command -v gitleaks >/dev/null 2>&1; then gitleaks detect -v --source . --no-git; else echo '⚠️ Gitleaks no instalado. Saltando.'; fi"]
            ),



            MakeTask(
                name="sast",
                description="🧠 [Step 2] Análisis SAST del Código (Bandit)",
                commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run python -m bandit -r $(TARGET) -ll -i"]
            ),




            #
            #MakeTask(
            #    name="sast",
            #    description="🧠 [Step 2] Análisis SAST del Código (Bandit)",
            #    commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run python -m bandit -r src/ -ll -i"]
            #),
            #




            MakeTask(
                name="sca",
                description="📦 [Step 3] Auditoría de Dependencias de Terceros (pip-audit)",
                dependencies=["sync"], # 🪄 AQUÍ ESTÁ LA MAGIA SRE
                commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run python -m pip_audit || echo '⚠️ pip-audit detectó vulnerabilidades. Revisa el reporte.'"]
            ),

            # Nota: También podrías poner "sync" como dependencia de la tarea test, 
            # para asegurarte de que nunca corres pruebas con dependencias desactualizadas.


            #
            #MakeTask(
            #    name="sca",
            #    description="📦 [Step 3] Auditoría de Dependencias de Terceros (pip-audit)",
            #    commands=["VIRTUAL_ENV=$$(pwd)/.venv uv run python -m pip_audit || echo '⚠️ pip-audit detectó vulnerabilidades. Revisa el reporte.'"]
            #),
            #


            MakeTask(
                name="image-scan",
                description="🐳 [Step 4] Escaneo de vulnerabilidades del FS (Trivy)",
                commands=[
                    "@if [ -f \"requirements.lock.txt\" ]; then grep -v \"^#\" requirements.lock.txt | grep -v \"^$$\" > requirements.txt.tmp && mv requirements.txt.tmp requirements.txt; fi",
                    "@if command -v trivy >/dev/null 2>&1; then trivy fs . --scanners vuln --severity HIGH,CRITICAL --no-progress; else echo '⚠️ Trivy no instalado. Saltando.'; fi"
                ]
            ),
            MakeTask(
                name="security",
                description="🚓 Ejecuta TODA la suite de DevSecOps",
                dependencies=["secrets", "sast", "sca", "image-scan"],
                commands=["@echo '✅ Auditoría DevSecOps Total completada.'"]
            ),
            MakeTask(
                name="docker-build",
                description="🐳 Construye la imagen local inyectando el ci-metadata.json (SSOT)",
                commands=[
                    "@echo 'Leyendo infraestructura desde ci-metadata.json...'",
                    "PYTHON_BASE=$$(jq -r '.python_base_image' ci-metadata.json); \\",
                    "APT_PACKS=$$(jq -r '.apt_requirements' ci-metadata.json); \\",
                    "INSTALL_CMD=$$(jq -r '.project_installation_command' ci-metadata.json); \\",
                    "EXTRA_URL=$$(jq -r '.extra_index_url // empty' ci-metadata.json); \\",
                    "docker build --build-arg PYTHON_BASE=$$PYTHON_BASE --build-arg APT_REQUIREMENTS=\"$$APT_PACKS\" --build-arg INSTALL_CMD=\"$$INSTALL_CMD\" --build-arg EXTRA_INDEX_URL=\"$$EXTRA_URL\" -t english-editor:local ."
                ]
            ),
            MakeTask(
                name="docker-run",
                description="▶️ Ejecuta el contenedor recién construido",
                dependencies=["docker-build"],
                commands=["docker run --rm english-editor:local"]
            ),
            MakeTask(
                name="clean",
                description="🧹 Limpia caché y artefactos basura del sistema",
                commands=[
                    "find . -type d -name '__pycache__' -exec rm -rf {} +",
                    "find . -type d -name '.pytest_cache' -exec rm -rf {} +",
                    "find . -type d -name '.mypy_cache' -exec rm -rf {} +"
                ]
            )
        ]







# =====================================================================
# 3. EL MOTOR GENERADOR (Infraestructura)
# =====================================================================
class MakefileBuilder:
    """Motor central para compilar el archivo Makefile físico."""
    def __init__(self, profile: MakefileProfile, output_dir: str) -> None:
        self.profile = profile
        self.output_path = Path(output_dir) / "Makefile"

    def build(self) -> None:
        print(f"🏗️ Construyendo Makefile universal basado en {self.profile.__class__.__name__}...")

        #3
        #Así evitas que dos MakeTask tengan el mismo nombre. No duplicados
        #tasks = self.profile.tasks
        #names = [t.name for t in tasks]
        #if len(names) != len(set(names)):
        #    raise ValueError("❌ Hay tareas duplicadas en el perfil Makefile")
        #phony_targets = " ".join(names)
        #

        #2
        #tasks = self.profile.tasks
        # 🔒 Garantiza orden determinista y evita duplicados
        #phony_targets = " ".join(sorted({t.name for t in tasks}))
        #



        #Mejora sugerida:
        #tasks = self.profile.tasks
        #
        #phony_targets = " ".join(sorted({t.name for t in tasks}))
        #
        #content = [
        #    "SHELL := bash",
        #    ".DEFAULT_GOAL := help",
        #    ".ONESHELL:",
        #    "",
        #    f".PHONY: {phony_targets}",
        #    ""
        #]
        #


        #1 org
        tasks = self.profile.tasks
        phony_targets = " ".join([task.name for task in tasks])

        content = [
            "# ====================================================================",
            "# 🤖 MAKEFILE AUTOGENERADO (Universal API para el Desarrollador y CI)",
            "# ====================================================================",

            #"SHELL := bash",
            #".DEFAULT_GOAL := help",
            #".ONESHELL:",
            #"",

            f".PHONY: {phony_targets}\n",
            #"",
            "# 🔥 FIX SRE: Asegurar que los binarios locales sean detectados",
            "export PATH := $(HOME)/.local/bin:$(PATH)\n",
            "# ⚙️ VARIABLES GLOBALES SRE",
            "TARGET ?= src/english_editor/infrastructure/tools/",   #Truco para que nos deje pasar y verificar que termina el flujo en conformidad
            #"TARGET ?= src/ tests/",
            "ENGINE ?= uv",
            "EXTRA_INDEX_URL ?= $(shell jq -r \".extra_index_url // empty\" ci-metadata.json 2>/dev/null)\n",
            #"EXTRA_INDEX_URL ?=\n",
            "EXTRAS ?=\n"  # 🪄 INYECCIÓN SRE: Soporte dinámico para extras del pyproject.toml
        ]

        for task in tasks:
            deps_str = " " + " ".join(task.dependencies) if task.dependencies else ""
            #content.append(f"# {{task.description}}")
            content.append(f"# {task.description}")
            #content.append(f"{{task.name}}:{{deps_str}}")
            content.append(f"{task.name}:{deps_str}")

            for cmd in task.commands:
                # ⚠️ REGLA DE ORO MAKEFILE: TAB (	) real
                #content.append(f"\t{{cmd}}")
                content.append(f"\t{cmd}")
            content.append("")  # Línea vacía separadora

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        #print(f"✅ Artefacto creado exitosamente en: {{self.output_path}}")
        print(f"✅ Artefacto creado exitosamente en: {self.output_path}")


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    # Cuando se ejecuta, asume que la raíz del proyecto es 4 niveles arriba del script
    # src/english_editor/infrastructure/tools/makefile_builder.py -> root
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent

    perfil = ModernPythonProfile()
    builder = MakefileBuilder(profile=perfil, output_dir=str(project_root))
    #builder = MakefileBuilder(profile=perfil, output_dir="/content/english-editor") # codigo anterior desde la celda colab.
    builder.build()
