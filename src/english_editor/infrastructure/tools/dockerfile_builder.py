"""
Motor agnóstico generador de Dockerfiles SRE (OOP).
Responsabilidad: Generar programáticamente archivos Dockerfile estandarizados,
basados en perfiles de arquitectura (API, CLI, ML).
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

# =====================================================================
# 1. ENTIDADES DE DOMINIO
# =====================================================================
@dataclass
class DockerStage:
    """Representa una fase lógica dentro del Dockerfile."""
    name: str
    description: str
    commands: list[str]

# =====================================================================
# 2. EL PATRÓN STRATEGY: Perfiles de Arquitectura
# =====================================================================
class DockerfileProfile(ABC):
    """Interfaz base para cualquier perfil de contenedor."""
    @property
    @abstractmethod
    def stages(self) -> list[DockerStage]:
        pass

# ---------------------------------------------------------------------
# Implementación Específica: Perfil CLI con Machine Learning (Offline)
# ---------------------------------------------------------------------
class MLCLIProfile(DockerfileProfile):
    """Perfil DevSecOps para aplicaciones CLI con IA (Whisper) y soporte Offline."""

    @property
    def stages(self) -> list[DockerStage]:
        return [




            DockerStage(
                name="BASE",
                description="1. BASE IMAGE Y SISTEMA OPERATIVO",
                commands=[
                    "ARG PYTHON_BASE=python:3.12-slim",
                    "FROM ${PYTHON_BASE}",
                    "",
                    "# [ASPECTO CRÍTICO 2]: Zona Horaria (Timezone)",
                    "ENV TZ=\"America/Bogota\"",
                    "RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone",
                    "",
                    "# Dependencias del Sistema Operativo inyectadas desde CI/CD",
                    "ARG APT_REQUIREMENTS=\"\"",
                    "RUN apt-get update && apt-get install -y --no-install-recommends \\",
                    "    ${APT_REQUIREMENTS} \\",
                    "    && rm -rf /var/lib/apt/lists/*"
                ]
            ),
            DockerStage(
                name="SECURITY",
                description="2. SEGURIDAD Y PERMISOS (El Error Silencioso)",
                commands=[
                    "# Creamos un usuario no-root por seguridad.",
                    "RUN useradd -m appuser",
                    "WORKDIR /app",
                    "",
                    "# [ASPECTO CRÍTICO 1]: Permisos de Escritura en Volúmenes",
                    "RUN mkdir -p /app/data /home/appuser/.cache \\",
                    "    && chown -R appuser:appuser /app /home/appuser"
                ]
            ),
            DockerStage(
                name="PYTHON_LAYER",
                description="3. INSTALACIÓN DE DEPENDENCIAS (Python Layer)",
                commands=[
                    "RUN pip install --no-cache-dir --upgrade pip setuptools wheel",
                    "",
                    "# Capa 1: SSOT de Producción (Con Hashes)",
                    "COPY --chown=appuser:appuser requirements.lock.txt requirements.txt",
                    "RUN pip install --no-cache-dir -r requirements.txt",
                    "",
                    "# Capa 2: Código fuente del negocio",
                    "COPY --chown=appuser:appuser src/ src/",
                    "COPY --chown=appuser:appuser pyproject.toml .",
                    "",
                    "# Capa 3: Instalación del paquete",
                    "ARG INSTALL_CMD=\"pip install --no-cache-dir --no-deps .\"",
                    "RUN ${INSTALL_CMD}"
                ]
            ),
            DockerStage(
                name="USER_MODE",
                description="4. OPERACIONES DE USUARIO Y MODO OFFLINE",
                commands=[
                    "USER appuser",
                    "",
                    "# [OPCIÓN 2 APLICADA]: Inmortalidad Offline para IA",
                    "RUN python -c \"import whisper; whisper.load_model('tiny.en'); whisper.load_model('base.en')\""
                ]
            ),
            DockerStage(
                name="ENTRYPOINT",
                description="5. ARRANQUE DE LA APLICACIÓN",
                commands=[
                    "# [ASPECTO CRÍTICO 3]: El Síndrome de Procesos Zombie (Formato Exec)",
                    "ENTRYPOINT [\"python\", \"-m\", \"english_editor.modules.analysis.presentation.cli\"]"
                ]
            )
        ]

# =====================================================================
# 3. EL MOTOR GENERADOR
# =====================================================================
class DockerfileBuilder:
    """Motor central para compilar el archivo Dockerfile físico."""
    def __init__(self, profile: DockerfileProfile, output_dir: str) -> None:
        self.profile = profile
        self.output_path = Path(output_dir) / "Dockerfile"

    def build(self) -> None:
        print(f"🏗️ Construyendo Dockerfile basado en {self.profile.__class__.__name__}...")

        content = [
            "# ==============================================================================",
            "# 🐳 DOCKERFILE UNIVERSAL DEVSECOPS (Generado Automáticamente)",
            "# Propósito: Empaquetar aplicaciones Python bajo estándares SRE y PyPA.",
            "# ==============================================================================",
            ""
        ]

        for stage in self.profile.stages:
            content.append("# ------------------------------------------------------------------------------")
            content.append(f"# {stage.description}")
            content.append("# ------------------------------------------------------------------------------")
            for cmd in stage.commands:
                content.append(cmd)
            content.append("") # Separador visual entre bloques

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        print(f"✅ Dockerfile compilado exitosamente en: {self.output_path}")

# === Ejecución SRE ===
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    perfil = MLCLIProfile()
    builder = DockerfileBuilder(profile=perfil, output_dir=str(project_root))
    builder.build()
