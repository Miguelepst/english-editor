# src/english_editor/infrastructure/tools/dependency_manager.py
"""
Motor agnóstico de resolución de dependencias (Multi-Engine: uv / pip-tools).
Genera toda la suite de archivos, hashes criptográficos, metadata y auto-sana pre-commit.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from abc import ABC, abstractmethod
from pathlib import Path

import tomllib


class ProjectProfile(ABC):
    @property
    @abstractmethod
    def python_version(self) -> str: pass
    @property
    @abstractmethod
    def os_dependencies(self) -> list[str]: pass
    @property
    @abstractmethod
    def ci_blacklist(self) -> list[str]: pass
    @abstractmethod
    def should_exclude_package(self, line: str, hardware_target: str) -> bool: pass


    @property
    @abstractmethod
    def compiler_flags(self) -> list[str]:
        """Banderas inyectables específicas para el motor de compilación."""
        pass


class AudioEditorProfile(ProjectProfile):
    @property
    def python_version(self) -> str: return "3.12"
    @property
    def os_dependencies(self) -> list[str]: return ["ffmpeg", "libsndfile1", "build-essential", "git"]
    @property
    def ci_blacklist(self) -> list[str]: return []


    @property
    def compiler_flags(self) -> list[str]:
        # 🧠 INYECCIÓN DE REGLA DE NEGOCIO:
        # Permitimos a 'uv' mezclar el repo de PyTorch con PyPI
        return ["--index-strategy", "unsafe-best-match", "--python-version", self.python_version]
        #return ["--index-strategy", "unsafe-best-match"]

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



    def _update_pre_commit_hooks(self):
        pre_commit_config = self.base_dir / ".pre-commit-config.yaml"
        if pre_commit_config.exists():
            print("\n🧹 Auto-sanando configuración de pre-commit...")
            try:
                # 1. Asegurar que la herramienta existe en el entorno temporal
                subprocess.run([sys.executable, "-m", "pip", "install", "pre-commit", "--quiet"], check=False)

                # 2. Ejecutar la actualización capturando errores reales
                result = subprocess.run([sys.executable, "-m", "pre_commit", "autoupdate"], cwd=self.base_dir, check=False)

                # 3. Validar el Exit Code real
                if result.returncode == 0:
                    print("   ✔️ Hooks de Git actualizados a su última versión.")
                else:
                    print("   ⚠️ 'pre-commit autoupdate' terminó con advertencias o no se pudo ejecutar.")
            except Exception as e:
                print(f"   ⚠️ Error crítico al actualizar pre-commit: {e}")




    def _audit_project_structure(self) -> str:
        print("\n🔍 Iniciando auditoría de arquitectura (Shift-Left)...")
        if (self.base_dir / "src").exists() and self.target_pyproject.exists():
            print("   🏛️ Arquitectura detectada: 'src-layout' (Estándar PyPA).")
            return "pip install --no-cache-dir --no-deps ."
        return "ENV PYTHONPATH='/app'"





    def generate_ci_metadata(self, hardware_target: str, installation_command: str):
        metadata = {
            "project_name": self.project_name,
            "python_base_image": f"python:{self.profile.python_version}-slim",
            "apt_requirements": " ".join(self.profile.os_dependencies),
            "hardware_target": hardware_target,
            "project_installation_command": installation_command,
            # INYECCIÓN SRE: Guardamos el mapa de la bóveda
            "extra_index_url": "https://download.pytorch.org/whl/cpu" if hardware_target == "cpu" else ""
        }
        meta_path = self.base_dir / "ci-metadata.json"
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=4)

        print(f"\n   📄 Manifiesto de infraestructura actualizado: {meta_path.name}")





    def _clean_requirements(self, filepath: Path, hardware_target: str, is_ci: bool = False):
        if not filepath.exists():
            return

        #with open(filepath, "r", encoding="utf-8") as f:
        with open(filepath, encoding="utf-8") as f:
            lines = f.readlines()

        with open(filepath, "w", encoding="utf-8") as f:
            skip_mode = False
            for line in lines:
                line_stripped = line.strip()

                # 🛡️ FIX SRE: Lógica de escape estricta
                if skip_mode:
                    # Si es un hash, comentario o línea vacía, seguimos devorando
                    if line_stripped.startswith("--hash") or line_stripped.startswith("#") or not line_stripped or line_stripped == "\\":
                        continue
                    # Si llegamos aquí, es texto normal (un paquete nuevo). Apagamos el hoyo negro.
                    skip_mode = False

                if self.profile.should_exclude_package(line_stripped, hardware_target):
                    skip_mode = True
                    continue

                if is_ci and any(line_stripped.startswith(bp) for bp in self.profile.ci_blacklist):
                    skip_mode = True
                    continue

                if not skip_mode:
                    f.write(line)









    """#v
    def _clean_requirements(self, filepath: Path, hardware_target: str, is_ci: bool = False):
        if not filepath.exists():
            return

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        with open(filepath, "w", encoding="utf-8") as f:
            skip_mode = False
            for line in lines:
                line_stripped = line.strip()
                if skip_mode:
                    if any(line_stripped.startswith(s) for s in ["--hash", "#", "\\"]) or line_stripped.endswith("\\"):
                        continue
                    skip_mode = False

                if self.profile.should_exclude_package(line_stripped, hardware_target):
                    skip_mode = True
                    continue

                if is_ci and any(line_stripped.startswith(bp) for bp in self.profile.ci_blacklist):
                    skip_mode = True
                    continue

                if not skip_mode:
                    f.write(line)
    #"""




    def generate_requirements(self, engine: str = "uv", hardware_target: str = "cpu"):
        installation_cmd = self._audit_project_structure()

        prod_path = self.base_dir / "requirements.txt"
        ci_path = self.base_dir / "requirements-ci.txt"
        dev_path = self.base_dir / "requirements-dev.txt"
        lock_path = self.base_dir / "requirements.lock.txt"

        index_url = "https://download.pytorch.org/whl/cpu" if hardware_target == "cpu" else ""
        print(f"\n🚀 Iniciando Motor: {engine.upper()} | Target: {hardware_target}")

        try:
            # 1. Leer extras del pyproject.toml
            config = {}
            try:
                with open(self.target_pyproject, "rb") as f:
                    config = tomllib.load(f)

            except Exception:
                pass

            all_extras = config.get("project", {}).get("optional-dependencies", {}).keys()
            dev_patterns = {"dev", "test", "docs", "lint", "typing", "ci"}

            prod_extras = [ext for ext in all_extras if ext.lower() not in dev_patterns]
            prod_flags = []
            for ext in prod_extras:
                prod_flags.extend(["--extra", ext])

            ci_flags = prod_flags.copy()
            for ext in ["test", "dev", "security"]:
                if ext in all_extras:
                    ci_flags.extend(["--extra", ext])

            # 2. Configurar Comandos Base
            base_cmd = []



            if engine == "uv":
                subprocess.run([sys.executable, "-m", "pip", "install", "uv", "--quiet"], check=False)
                 # 🏗️ ARQUITECTURA PURA: Comando base sin castigos de caché

                # fue un fix erroneo, Le inyectamos la orden estricta de NO USAR CACHÉ (--refresh) pero se pierde velocidad rust.
                #base_cmd = ["python", "-m", "uv", "pip", "compile", str(self.target_pyproject), "--generate-hashes", "--refresh"]

                ## Limpio y universal:
                base_cmd = ["python", "-m", "uv", "pip", "compile", str(self.target_pyproject), "--generate-hashes"]
                # Dinámico e inteligente:
                base_cmd.extend(self.profile.compiler_flags)






            #if engine == "uv":
            #    subprocess.run([sys.executable, "-m", "pip", "install", "uv", "--quiet"], check=False)
            #    base_cmd = ["python", "-m", "uv", "pip", "compile", str(self.target_pyproject), "--generate-hashes", "--index-strategy", "unsafe-best-match"]
            #    #base_cmd = ["python", "-m", "uv", "pip", "compile", str(self.target_pyproject), "--generate-hashes"]
            #    # 💉 Inyectamos dinámicamente las banderas del perfil actual
            #    base_cmd.extend(self.profile.compiler_flags)


            elif engine == "pip-tools-fast":
                subprocess.run([sys.executable, "-m", "pip", "install", "pip-tools", "--quiet"], check=False)
                base_cmd = [sys.executable, "-m", "piptools", "compile", "--generate-hashes", "--reuse-hashes", "--strip-extras", "--quiet"]
            else:
                subprocess.run([sys.executable, "-m", "pip", "install", "pip-tools", "--quiet"], check=False)
                base_cmd = [sys.executable, "-m", "piptools", "compile", "--generate-hashes", "--quiet"]


            if index_url:
                base_cmd.extend(["--extra-index-url", index_url])

            # 3. Compilación Implacable
            print("\n   📦 Compilando Producción...")
            subprocess.run(base_cmd + prod_flags + ["-o", str(prod_path)], check=True)
            self._clean_requirements(prod_path, hardware_target)

            print("   🛠️ Compilando CI...")
            subprocess.run(base_cmd + ci_flags + ["-o", str(ci_path)], check=True)
            self._clean_requirements(ci_path, hardware_target, is_ci=True)

            print("   🔬 Compilando Desarrollo (All-Extras)...")
            subprocess.run(base_cmd + ["--all-extras", "-o", str(dev_path)], check=True)
            self._clean_requirements(dev_path, hardware_target)





            # ❌ Lo que tenías (Contaminaba Producción con herramientas de Dev):
            # print("   🔒 Sellando Lockfile Maestro (SSOT)...")
            # shutil.copy(dev_path, lock_path)

            # ✅ La Buena Práctica (Sella Producción pura con Hashes para Docker):
            print("   🔒 Sellando Lockfile Maestro para Producción (SSOT)...")
            shutil.copy(prod_path, lock_path)





            #print("   🔒 Sellando Lockfile Maestro (SSOT)...")
            #shutil.copy(dev_path, lock_path)

            # 4. Restauración de Funcionalidades Auxiliares (Sin Regresiones)
            self.generate_ci_metadata(hardware_target, installation_cmd)
            self._update_pre_commit_hooks()

            print("\n✅ ¡Éxito! Infraestructura completa generada y asegurada.")
        except Exception as e:
            print(f"\n❌ Error en la generación: {e}")

if __name__ == "__main__":
    selected_engine = os.environ.get("ENGINE", "").strip() or "uv"
    #selected_engine = os.environ.get("ENGINE", "uv")
    perfil = AudioEditorProfile()
    mgr = DependencyManager(perfil, "/content/english-editor/pyproject.toml")
    mgr.generate_requirements(engine=selected_engine)
