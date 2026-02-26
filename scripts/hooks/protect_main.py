# scripts/hooks/protect_main.py
"""
Protección educativa de rama main.

Arquitectura: Modular Monolith + Vertical Slice
Componente: hook/pre-commit
Responsabilidad: Detectar intentos de commit en 'main' y guiar al desarrollador.
"""
from __future__ import annotations

# === 🧭 Protocolos Arquitectónicos (Strict Layering) ===
# ✅ HOOKS: Scripts auxiliares que operan en contexto Git.
# ✅ SYSTEM: Uso de subprocess para interoperar con Git CLI.
# ❌ DOMAIN LOGIC: Prohibido aquí (este script es de infraestructura de desarrollo).
# ❌ IMPORTS DEL PROYECTO: Prohibido (los hooks deben ser autocontenidos).
# === 🧪 Protocolos de Calidad Obligatorios ===
# 🔒 Side-effects controlados: Solo lectura de estado Git (rev-parse).
# 🧪 Testabilidad: Lógica modular en main() y funciones de apoyo.
# 🔤 Type Hints: Firmas con tipos explícitos para claridad.
# ⚡ Pureza: get_current_branch() es determinista según el estado de HEAD.
# 🚫 Excepciones: Uso de sys.exit() para comunicar el estado a pre-commit.
# 📏 Longitud de línea: Máximo 88 caracteres.
import subprocess
import sys


def get_current_branch() -> str:
    """Obtiene el nombre de la rama actual vía Git CLI."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def print_warning() -> None:
    """Muestra el banner educativo si se intenta commitear en main."""
    border = "─" * 70
    print(f"\n{border}")
    print("⚠️  ¡ALTO! Estás a punto de commitear en la rama MAIN")
    print(f"{border}")
    print("\n💡 Flujo Git recomendado para este proyecto:")
    print("   1️⃣  Cancela este commit: Presiona Ctrl+C")
    print("   2️⃣  Crea una rama descriptiva:")
    print("       git checkout -b feature/tu-nueva-funcionalidad")
    print("   3️⃣  Trabaja en tu rama: edita, commitea, prueba")
    print("   4️⃣  Push y crea PR en GitHub:")
    print("       git push origin feature/tu-nueva-funcionalidad")
    print("\n🔒 Esta protección mantiene la integridad del historial.")
    print(f"{border}\n")


def main() -> int:
    try:
        branch = get_current_branch()
    except Exception:
        # Si Git falla, permitimos el commit para no bloquear.
        return 0

    if branch == "main":
        print_warning()
        # MODO EDUCATIVO: Retornamos 0 para avisar pero no bloquear.
        # Cambiar a 'return 1' para bloqueo estricto.
        # print("✅ Modo educativo: Continuando con el commit (solo advertencia)\n")
        # return 0

        # ❌ OPCIÓN B: Bloquear realmente
        print("❌ Commit bloqueado. Crea una rama primero.")
        return 1  # ← Al fallar, pre-commit MOSTRARÁ obligatoriamente tu banner

    return 0


if __name__ == "__main__":
    sys.exit(main())
