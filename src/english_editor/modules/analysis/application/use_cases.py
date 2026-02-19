# src/english_editor/modules/analysis/application/use_cases.py
"""
Casos de Uso para el Análisis de Audio.

Arquitectura: Application Layer
Responsabilidad: Orquestar la detección de voz delegando en la infraestructura.
"""
from __future__ import annotations
from typing import List
from pathlib import Path

from english_editor.modules.analysis.domain.value_objects import TimeRange
from english_editor.modules.analysis.domain.ports.engine import SpeechAnalysisEngine
from english_editor.modules.analysis.domain.exceptions import AudioFileError

# ✅ Nuevo Import de Infraestructura (Observabilidad)
from english_editor.modules.analysis.infrastructure.observability import ObservabilityService

class AnalyzeAudio:
    """
    Caso de Uso: Analizar un archivo de audio para detectar segmentos de voz.

    Colaboradores:
    - engine: SpeechAnalysisEngine (Puerto)
    """

    def __init__(self, engine: SpeechAnalysisEngine):
        """
        Inyectar la implementación del motor (Dependency Injection).
        """
        self._engine = engine

    # ✅ Instrumentación: Medimos "Latency" y "Errors" automáticamente
    @ObservabilityService.measure_latency(operation_name="analyze_audio_use_case")
    def execute(self, file_path: Path) -> List[TimeRange]:
        """
        Ejecuta el análisis sobre el archivo indicado.

        Args:
            file_path: Ruta absoluta o relativa al archivo de audio.

        Returns:
            Lista de TimeRange con los segmentos de voz detectados.

        Raises:
            AudioFileError: Si el archivo no existe o no es válido.
            AnalysisError: Si falla el motor.
        """
        # 1. Validación de Capa de Aplicación (Fail Fast)
        if not file_path.exists():
            raise AudioFileError(f"El archivo no existe: {file_path}")

        if not file_path.is_file():
             raise AudioFileError(f"La ruta no es un archivo: {file_path}")

        # 2. Delegación al Dominio/Infraestructura
        # Nota: El motor (whisper) se encargará del chunking y la RAM internamente.
        segments = self._engine.detect_voice_activity(file_path)

        # 3. (Opcional) Aquí podríamos agregar lógica de post-procesamiento
        # como mergear segmentos muy cercanos si la UI lo requiere.

        # 3. Métricas de Negocio (Loguear resultado)
        # Nota: Podríamos loguear aquí cuántos segmentos se encontraron
        # pero el decorador ya captura el éxito.

        return segments