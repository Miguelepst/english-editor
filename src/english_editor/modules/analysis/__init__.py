
# @title 📦 __init__.py — [Analysis Module]
# ✅ Init creado: /content/english-editor/src/english_editor/modules/analysis/__init__.py

# src/english_editor/modules/analysis/__init__.py
"""
Módulo de Análisis de Audio.

Responsabilidades:
1. Inferencia local con Whisper (CPU).
2. Segmentación de voz (VAD).
3. Gestión de memoria eficiente (Chunking).
"""

from __future__ import annotations

# Exponemos los Value Objects principales para otros módulos
from .domain.value_objects import TimeRange

__all__ = ["TimeRange"]


