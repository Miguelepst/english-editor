#!/usr/bin/env python3
"""
Pipeline de CI Local para el Proyecto English Editor.
Ejecuta validaciones estáticas, tests unitarios y de integración.

Uso: python scripts/ci_pipeline.py
"""

# orden incorrecto de imports
# from datetime import datetime
# import subprocess
# import sys
# import time

import subprocess  # ← 'import' primero, orden alfabético: s, s, t
import sys
import time
from datetime import datetime  # ← 'from' después, orden alfabético: d


# Colores para la terminal
class Colors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_step(step_name):
    print(f"\n{Colors.HEADER}=== EJECUTANDO: {step_name} ==={Colors.ENDC}")


def run_command(command, description):
    print(f"⏳ {description}...")
    start = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    duration = time.time() - start

    if result.returncode == 0:
        print(f"{Colors.OKGREEN}✅ PASÓ ({duration:.2f}s){Colors.ENDC}")
        return True, result.stdout
    else:
        print(f"{Colors.FAIL}❌ FALLÓ ({duration:.2f}s){Colors.ENDC}")
        print(f"{Colors.WARNING}--- STDERR ---\n{result.stderr}{Colors.ENDC}")
        print(f"{Colors.WARNING}--- STDOUT ---\n{result.stdout}{Colors.ENDC}")
        return False, result.stderr


def main():
    start_total = time.time()
    print(
        f"{Colors.BOLD}🚀 INICIANDO PIPELINE CI/CD - SPS 01: ORCHESTRATION{Colors.ENDC}"
    )
    print(f"📅 Fecha: {datetime.now()}")

    # steps = []   #rufus

    # --- PASO 1: LINTER (Estilo) ---
    # Usamos Ruff si está instalado, o skip
    print_step("1. ANÁLISIS ESTÁTICO DE CÓDIGO (LINTING)")
    success, _ = run_command(
        "ruff check src/ tests/",
        "Verificando estilo de código (PEP8) y errores comunes",
    )
    if not success:
        # No fallamos el build por estilo aun, pero avisamos
        print(
            f"{Colors.WARNING}⚠️  Advertencias de estilo detectadas (No bloqueante por ahora){Colors.ENDC}"
        )

    # --- PASO 2: TYPE CHECKING (MyPy) ---
    print_step("2. VERIFICACIÓN DE TIPOS (DDD STRICTNESS)")
    # Verificamos solo el dominio para asegurar contratos fuertes
    success, _ = run_command(
        "mypy src/english_editor/modules/orchestration/domain --ignore-missing-imports",
        "Validando tipos estrictos en el Dominio",
    )
    if not success:
        print(f"{Colors.FAIL}⛔ El dominio viola el contrato de tipos.{Colors.ENDC}")
        sys.exit(1)

    # --- PASO 3: TESTS UNITARIOS ---
    print_step("3. TESTS UNITARIOS (DOMAIN & APP)")
    # Excluimos E2E e Infraestructura pesada
    success, _ = run_command(
        "pytest tests/modules/orchestration/domain tests/modules/orchestration/application -v",
        "Ejecutando lógica pura de negocio",
    )
    if not success:
        sys.exit(1)

    # --- PASO 4: TESTS INTEGRACIÓN & E2E ---
    print_step("4. TESTS E2E & INFRAESTRUCTURA (HEAVY LOAD)")
    success, _ = run_command(
        "pytest tests/modules/orchestration/infrastructure tests/e2e -v",
        "Validando persistencia real y archivos grandes",
    )
    if not success:
        sys.exit(1)

    # --- RESUMEN ---
    total_duration = time.time() - start_total
    print(f"\n{Colors.OKGREEN}{'='*50}{Colors.ENDC}")
    print(f"{Colors.OKGREEN}🎉  BUILD SUCCESSFUL - CALIDAD CERTIFICADA{Colors.ENDC}")
    print(f"{Colors.OKGREEN}{'='*50}{Colors.ENDC}")
    print(f"⏱️ Tiempo Total: {total_duration:.2f}s")


if __name__ == "__main__":
    main()
