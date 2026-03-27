
# @title 📦 __init__.py — [Update Module Facade]
# ✅ Facade actualizado: /content/english-editor/src/english_editor/modules/analysis/__init__.py

# src/english_editor/modules/analysis/__init__.py
"""
Módulo de Análisis de Audio.

Responsabilidades:
1. Inferencia local con Whisper (CPU).
2. Segmentación de voz (VAD).
3. Gestión de memoria eficiente (Chunking).
"""

from __future__ import annotations

from .domain.exceptions import AnalysisError, AudioFileError, MemoryLimitExceeded

# Domain Ports & Exceptions (Contrato público para Application Layer)
from .domain.ports.engine import SpeechAnalysisEngine

# Domain Primitives
from .domain.value_objects import TimeRange

__all__ = [
    "TimeRange",
    "SpeechAnalysisEngine",
    "AnalysisError",
    "AudioFileError",
    "MemoryLimitExceeded",
]

