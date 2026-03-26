
# @title 📦 __init__.py — [Facade] Contrato Público de Infrastructure
# ✅ __init__.py creado/actualizado: /content/english-editor/src/english_editor/modules/renderer/infrastructure/__init__.py

# src/english_editor/modules/renderer/infrastructure/__init__.py
"""
Contrato Público de la Capa de Infraestructura (Renderer).

✨ Rol arquitectónico: Contrato Público (Facade)
⚠️  PROHIBIDO: Lógica de negocio de dominio.
✅ PERMITIDO: Re-exportación de adaptadores concretos.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# === 📦 IMPORTS DE RE-EXPORTACIÓN (FACADE) ===
from .adapters import FFmpegMediaSplicer

# === 🌐 DEFINICIÓN DE INTERFAZ PÚBLICA (API CONTRACT) ===
__all__ = [
    "FFmpegMediaSplicer",
]


