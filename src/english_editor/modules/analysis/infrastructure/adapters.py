# src/english_editor/modules/analysis/infrastructure/adapters.py
"""
Adaptadores de Infraestructura para Análisis de Audio.

Arquitectura: Infrastructure Layer
Responsabilidad: Implementar puertos del dominio usando tecnologías concretas (o Fakes).
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from english_editor.modules.analysis.domain.exceptions import AudioFileError
from english_editor.modules.analysis.domain.value_objects import TimeRange


class FakeSpeechEngine:
    """
    Implementación simulada (Fake) del motor de análisis.
    Útil para tests unitarios y desarrollo offline.

    Comportamiento:
    - Si el archivo contiene "empty", retorna lista vacía.
    - Si el archivo contiene "error", lanza AudioFileError.
    - Por defecto, retorna un rango fijo [0.0, 10.0].
    """

    def __init__(self, fixed_result: Optional[List[TimeRange]] = None):
        """
        Args:
            fixed_result: Si se provee, siempre retornará esta lista.
                          Si es None, usa lógica basada en el nombre del archivo.
        """
        self._fixed_result = fixed_result

    def detect_voice_activity(self, audio_path: Path) -> List[TimeRange]:
        """Simula la detección de voz."""

        # 1. Simular validación de existencia (aunque sea fake, debe parecer real)
        # Nota: En un test real, usualmente usamos tmp_path, así que el archivo existe.
        # Aquí solo simulamos el contrato.

        filename = audio_path.name.lower()

        # 2. Simular errores controlados
        if "error" in filename:
            raise AudioFileError(f"Simulando fallo de lectura para: {filename}")

        # 3. Retornar resultado fijo si fue inyectado
        if self._fixed_result is not None:
            return self._fixed_result

        # 4. Lógica dinámica para tests
        if "silence" in filename or "empty" in filename:
            return []

        # Default: Un segmento de 10 segundos
        return [TimeRange(0.0, 10.0)]
