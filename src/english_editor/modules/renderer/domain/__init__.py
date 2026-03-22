# src/english_editor/modules/renderer/domain/__init__.py
"""
Contrato Público del Dominio Renderer.

✨ Rol arquitectónico: Contrato Público (Facade)
⚠️  PROHIBIDO: Lógica de negocio, I/O, cálculos, o efectos secundarios.
✅ PERMITIDO: Imports de re-exportación, metadata estática, __all__ explícito.

📚 Protocolos cumplidos:
• Zero Logic: Este archivo SOLO declara interfaces, nunca ejecuta comportamiento
• Explicit Exports: __all__ define la superficie pública estable (API contract)
• Anti-Circular: Imports dentro de TYPE_CHECKING para evitar dependencias cíclicas
• Version Safety: Metadata estática (nunca lee __version__ desde otro módulo aquí)
"""
from __future__ import annotations

# === 🚫 PROTOCOLO ZERO LOGIC (ENFORZADO) ===
# Este archivo NUNCA debe contener:
#   ❌ if/else con lógica de negocio
#   ❌ llamadas a funciones (ej: connect_db(), load_config())
#   ❌ acceso a filesystem/red (ej: open(), requests.get())
#   ❌ cálculos complejos (ej: heavy_computation())
#   ❌ side effects (ej: print(), logging.basicConfig())
#
# ✅ Única excepción permitida: imports de re-exportación

# === 🔁 PROTOCOLO ANTI-CIRCULAR IMPORTS ===
# Para tipos en anotaciones sin romper dependencias:
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

# === 📦 IMPORTS DE RE-EXPORTACIÓN (FACADE) ===
# Aplana la estructura interna para consumidores externos
from .value_objects import Padding, MediaSegment

# === 🌐 DEFINICIÓN DE INTERFAZ PÚBLICA (API CONTRACT) ===
# __all__ es el contrato estable: cambiarlo = breaking change semver
__all__ = [
    "Padding",
    "MediaSegment",
]
