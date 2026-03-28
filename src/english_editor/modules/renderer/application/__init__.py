
# @title 📦 __init__.py — [Facade] Contrato Público de Application

# ⚠️  __init__.py ya existe (preservado): /content/english-editor/src/english_editor/modules/renderer/application/__init__.py
# src/english_editor/modules/renderer/application/__init__.py
"""
Contrato Público de la Capa de Aplicación (Renderer).

✨ Rol arquitectónico: Contrato Público (Facade)
⚠️  PROHIBIDO: Lógica de negocio, I/O, cálculos, o efectos secundarios.
✅ PERMITIDO: Imports de re-exportación, metadata estática, __all__ explícito.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# === 📦 IMPORTS DE RE-EXPORTACIÓN (FACADE) ===
from .use_cases import RenderMediaUseCase

# === 🌐 DEFINICIÓN DE INTERFAZ PÚBLICA (API CONTRACT) ===
__all__ = [
    "RenderMediaUseCase",
]




