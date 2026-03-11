
"""
Motor agnóstico de resolución de dependencias con hashes criptográficos.
Arquitectura: Modular Monolith + Vertical Slice
Componente: Infra/Tooling
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import tomllib


class ProjectProfile(ABC):
    @property
    @abstractmethod
    def python_version(self) -> str:
        pass

    @property
    @abstractmethod
    def os_dependencies(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def ci_blacklist(self) -> list[str]:
        pass

    @abstractmethod
    def should_exclude_package(self, line: str, hardware_target: str) -> bool:
        pass

class AudioEditorProfile(ProjectProfile):
    @property
    def python_version(self) -> str:
        return "3.12"

    @property
    def os_dependencies(self) -> list[str]:
        return ["ffmpeg", "libsndfile1", "build-essential", "git"]

    @property
    def ci_blacklist(self) -> list[str]:
        return []

    def should_exclude_package(self, line: str, hardware_target: str) -> bool:
        if hardware_target.lower() == "cpu" and re.match(r"^triton==", line.strip()):
            return True
        return False

class DependencyManager:
    def __init__(self, profile: ProjectProfile, pyproject_path: str | Path):
        self.profile = profile
        self.target_pyproject = Path(pyproject_path)
        self.base_dir = self.target_pyproject.parent
        self.project_name = self.target_pyproject.parent.name

    def _audit_project_structure(self) -> str:
        print("\n🔍 Iniciando auditoría de arquitectura (Shift-Left)...")
        if (self.base_dir / "src").exists() and self.target_pyproject.exists():
            print("   🏛️ Arquitectura detectada: 'src-layout' (Estándar PyPA).")
            return "pip install --no-cache-dir --no-deps ."
        return "ENV PYTHONPATH='/app'"

    def _update_pre_commit_hooks(self):
        pre_commit_config = self.base_dir / ".pre-commit-config.yaml"
        if pre_commit_config.exists():
            print("\n🧹 Auto-sanando configuración de pre-commit...")
            try:
                subprocess.run([sys.executable, "-m", "pre_commit", "autoupdate"], cwd=self.base_dir, check=False)
                print("   ✔️ Hooks de Git actualizados a su última versión.")
            except Exception as e:
                print(f"   ⚠️ No se pudo auto-actualizar pre-commit: {e}")

    def _clean_requirements(self, filepath: Path, is_ci: bool = False, hardware_target: str = "cpu"):
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()
        with open(filepath, "w", encoding="utf-8") as f:
            skip_mode = False
            for line in lines:
                line_stripped = line.strip()
                if skip_mode:
                    if line_stripped.startswith("--hash") or line_stripped.startswith("#") or line_stripped == "\\" or line_stripped.endswith("\\"):
                        continue
                    else:
                        skip_mode = False

                if self.profile.should_exclude_package(line_stripped, hardware_target):
                    skip_mode = True
                    continue
                if is_ci and any(line_stripped.startswith(bp) for bp in self.profile.ci_blacklist):
                    skip_mode = True
                    continue

                if not skip_mode:
                    f.write(line)

    def generate_ci_metadata(self, hardware_target: str, installation_command: str):
        metadata = {
            "project_name": self.project_name,
            "python_base_image": f"python:{self.profile.python_version}-slim",
            "apt_requirements": " ".join(self.profile.os_dependencies),
            "hardware_target": hardware_target,
            "project_installation_command": installation_command
        }
        meta_path = self.base_dir / "ci-metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=4)
        print(f"   📄 Manifiesto de infraestructura actualizado: {meta_path.name}")

    def generate_requirements(self, hardware_target: str = "cpu", prod_extras_override: list[str] | None = None) -> Path | None:
        if not self.target_pyproject.exists():
            return None
        installation_command = self._audit_project_structure()

        prod_extras = prod_extras_override or []
        if not prod_extras_override:
            try:
                with open(self.target_pyproject, "rb") as f:
                    config = tomllib.load(f)
                all_extras = config.get("project", {}).get("optional-dependencies", {}).keys()
                dev_patterns = {"dev", "test", "docs", "lint", "typing", "ci"}
                prod_extras = [ext for ext in all_extras if ext.lower() not in dev_patterns]
            except Exception:
                pass

        index_flags = ["--extra-index-url", "https://download.pytorch.org/whl/cpu"] if hardware_target.lower() == "cpu" else []

        prod_path = self.base_dir / "requirements.txt"
        lock_path = self.base_dir / "requirements.lock.txt"

        print(f"\n🔒 Resolviendo ecosistema para '{self.project_name}' (Generando Hashes SRE)...")

        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "pip-tools", "pre-commit", "--quiet"], check=False)

            prod_flags = []
            for ext in prod_extras:
                prod_flags.extend(["--extra", ext])

            subprocess.run([sys.executable, "-m", "piptools", "compile", str(self.target_pyproject), "-o", str(prod_path), "--quiet"] + prod_flags + index_flags)
            self._clean_requirements(prod_path, hardware_target=hardware_target)

            print("   🛡️ Calculando Hashes SHA-256 para el Lockfile...")
            subprocess.run([sys.executable, "-m", "piptools", "compile", "--generate-hashes", str(self.target_pyproject), "-o", str(lock_path), "--all-extras", "--quiet"] + index_flags)
            self._clean_requirements(lock_path, hardware_target=hardware_target)

            self.generate_ci_metadata(hardware_target, installation_command)
            self._update_pre_commit_hooks()

            print("   ✅ ¡Éxito! Contrato de seguridad inmutable generado.")
            return lock_path
        except Exception as e:
            print(f"   ⚠️ Error inesperado: {e}")
            return None

if __name__ == "__main__":
    perfil_audio = AudioEditorProfile()
    generador = DependencyManager(profile=perfil_audio, pyproject_path="/content/english-editor/pyproject.toml")
    generador.generate_requirements(hardware_target="cpu")
