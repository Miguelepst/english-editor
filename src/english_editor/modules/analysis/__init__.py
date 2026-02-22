# src/english_editor/modules/analysis/__init__.py
"""
Módulo de Análisis de Audio.
"""

from __future__ import annotations

# Application
from .application.use_cases import AnalyzeAudio
from .domain.exceptions import AnalysisError, AudioFileError, MemoryLimitExceeded
from .domain.ports.engine import SpeechAnalysisEngine

# Domain
from .domain.value_objects import TimeRange

# Infrastructure
from .infrastructure.adapters import FakeSpeechEngine
from .infrastructure.whisper_adapter import WhisperLocalAdapter

__all__ = [
    "TimeRange",
    "SpeechAnalysisEngine",
    "AnalysisError",
    "AudioFileError",
    "MemoryLimitExceeded",
    "AnalyzeAudio",
    "FakeSpeechEngine",
    "WhisperLocalAdapter",
]
