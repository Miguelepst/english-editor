"""
Motor agnóstico generador de .gitignore SRE (OOP).
Responsabilidad: Generar programáticamente archivos .gitignore estandarizados,
basados en perfiles de proyecto para evitar la fuga de datos o artefactos.
"""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

# =====================================================================
# 1. ENTIDADES DE DOMINIO
# =====================================================================
@dataclass
class GitignoreSection:
    """Representa un bloque lógico de reglas dentro del .gitignore."""
    name: str
    rules: list[str]

# =====================================================================
# 2. EL PATRÓN STRATEGY: Perfiles de Proyecto
# =====================================================================
class GitignoreProfile(ABC):
    """Interfaz base para cualquier perfil de control de versiones."""
    @property
    @abstractmethod
    def sections(self) -> list[GitignoreSection]:
        pass

# ---------------------------------------------------------------------
# Implementación Específica: Perfil English Editor (Colab + ML + Python)
# ---------------------------------------------------------------------
class EnglishEditorProfile(GitignoreProfile):
    """Perfil DevSecOps que combina Python, IA, Colab y reglas de negocio."""
    
    @property
    def sections(self) -> list[GitignoreSection]:
        return [
            GitignoreSection(
                name="🐍 Python Cache & Entornos",
                rules=[
                    "__pycache__/",
                    "*.py[cod]",
                    "*$py.class",
                    ".venv/",
                    "venv/",
                    "env/",
                    "ENV/"
                ]
            ),
            GitignoreSection(
                name="☁️ Google Colab & Jupyter",
                rules=[
                    ".ipynb_checkpoints/",
                    "*.ipynb",
                    ".gdrive/",
                    ".drive_sync/",
                    "system_execution.log",
                    "*.log",
                    ".colab_safe_to_modify",
                    ".colab_env_restored"
                ]
            ),
            GitignoreSection(
                name="📦 Distribución & Build Artifacts",
                rules=[
                    "*.egg-info/",
                    "*.egg",
                    "dist/",
                    "build/",
                    "*.whl",
                    "*.tar.gz"
                ]
            ),
            GitignoreSection(
                name="🧪 Testing & Documentación",
                rules=[
                    ".coverage",
                    "htmlcov/",
                    ".coverage.*",
                    "coverage.xml",
                    ".pytest_cache/",
                    "site/  # MkDocs"
                ]
            ),
            GitignoreSection(
                name="🖼️ IDE & Archivos de Sistema",
                rules=[
                    ".vscode/",
                    ".idea/",
                    "*.swp",
                    "*.swo",
                    "*~",
                    "*.bak",
                    "*.orig",
                    "*.rej",
                    ".DS_Store",
                    "Thumbs.db"
                ]
            ),
            GitignoreSection(
                name="🔒 Secrets & Credentials (CRÍTICO)",
                rules=[
                    ".env",
                    "*.env",
                    "secrets/",
                    "credentials.json",
                    "token.pickle"
                ]
            ),
            GitignoreSection(
                name="📁 ML Assets, Media & Temporales",
                rules=[
                    "*.wav",
                    "*.mp3",
                    "*.mp4",
                    "output/",
                    "temp/",
                    "*.tmp",
                    "*.temp",
                    "*.npy",
                    "*.npz",
                    "*.h5",
                    "*.hdf5"
                ]
            ),
            GitignoreSection(
                name="🔄 Reglas de Negocio Específicas (Sandboxes)",
                rules=[
                    "checkpoints_*.json",
                    "*.checkpoint",
                    "sandbox_*/outputs/",
                    "sandbox_*/inputs/*.processed.*",
                    "sandbox_*/inputs/*_editado.*"
                ]
            ),
            GitignoreSection(
                name="✅ EXCEPCIONES EXPLÍCITAS (Fuerzan inclusión)",
                rules=[
                    "!sandbox_demo/checkpoints.json",
                    "!sandbox_observability/checkpoints.json",
                    "!assets/hello_world_2.mp4",
                    "!sample_data/",
                    "!sample_data/*.csv",
                    "!sample_data/*.json",
                    "!sample_data/README.md"
                ]
            )
        ]

# =====================================================================
# 3. EL MOTOR GENERADOR
# =====================================================================
class GitignoreBuilder:
    """Motor central para compilar el archivo .gitignore físico."""
    def __init__(self, profile: GitignoreProfile, output_dir: str) -> None:
        self.profile = profile
        self.output_path = Path(output_dir) / ".gitignore"

    def build(self) -> None:
        print(f"🏗️ Construyendo .gitignore basado en {self.profile.__class__.__name__}...")
        
        content = [
            "# ==============================================================================",
            "# 🙈 .GITIGNORE UNIVERSAL DEVSECOPS (Generado Automáticamente)",
            "# Propósito: Prevenir la fuga de secretos, binarios y artefactos locales.",
            "# ==============================================================================",
            ""
        ]

        for section in self.profile.sections:
            content.append(f"# ========================================")
            content.append(f"# {section.name}")
            content.append(f"# ========================================")
            for rule in section.rules:
                if rule.strip(): # Evita líneas vacías por error
                    content.append(rule)
            content.append("") # Separador visual entre bloques

        content.append("# ========================================")
        content.append("# 💡 Notas de Mantenimiento")
        content.append("# ========================================")
        content.append("# - Los checkpoints.json en sandboxes son parte del flujo controlado y deben versionarse.")
        content.append("# - Los outputs/ generados NO deben versionarse (son artefactos derivados).")
        content.append("# - Los assets de ejemplo documentados se mantienen para reproducibilidad.")
        content.append("# - sample_data/ contiene datasets de referencia para pruebas documentadas.")

        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        print(f"✅ Archivo .gitignore compilado exitosamente en: {self.output_path}")

# === Ejecución SRE ===
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent.parent.parent
    perfil = EnglishEditorProfile()
    builder = GitignoreBuilder(profile=perfil, output_dir=str(project_root))
    builder.build()
