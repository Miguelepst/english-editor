# src/english_editor/modules/analysis/domain/ports/engine.py
"""
Puerto para el Motor de Análisis de Voz.

Arquitectura: Domain Port (Interface)
Responsabilidad: Definir el contrato para la detección de actividad de voz (VAD).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from english_editor.modules.analysis.domain.value_objects import TimeRange


class SpeechAnalysisEngine(Protocol):
    """
    Contrato abstracto para motores de detección de voz e inferencia.

    Implementaciones esperadas:
    - WhisperLocalAdapter (Infraestructura)
    - FakeSpeechEngine (Testing)
    """

    def detect_voice_activity(self, audio_path: Path) -> list[TimeRange]:
        """
        Analiza un archivo de audio y retorna los rangos de tiempo donde
        se detecta habla humana inteligible.

        Args:
            audio_path: Ruta al archivo de audio fuente.

        Returns:
            Lista de TimeRanges válidos.

        Raises:
            AudioFileError: Si el archivo no es accesible.
            EngineRuntimeError: Si falla el motor de inferencia.
        """
        ...
