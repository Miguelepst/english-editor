# src/english_editor/modules/analysis/infrastructure/whisper_adapter.py
"""
Adaptador de infraestructura para Whisper (OpenAI).

Arquitectura: Infrastructure Layer
Responsabilidad: Implementar SpeechAnalysisEngine usando Whisper localmente.
"""

from __future__ import annotations

from pathlib import Path

# Imports de terceros (Solo permitidos en capa de infraestructura)
try:
    import librosa
    import numpy as np
    import torch
    import whisper
except ImportError:
    # Fallback para que el código sea importable sin dependencias instaladas (CI/CD)
    # whisper = None
    whisper = None  [assignment]
    # torch = None
    torch = None  [assignment]
    # librosa = None
    librosa = None  [assignment]
    # np = None
    np = None  [assignment]

from english_editor.modules.analysis.domain.exceptions import (
    AudioFileError,
    EngineRuntimeError,
    MemoryLimitExceeded,
)
from english_editor.modules.analysis.domain.value_objects import TimeRange


class WhisperLocalAdapter:
    """
    Implementación real usando el modelo 'tiny.en' de Whisper.
    Ejecución forzada en CPU y gestión de memoria por chunking.
    """

    # Configuración de chunking (Constantes de Infraestructura)
    CHUNK_DURATION_SEC = 600  # 10 minutos por ventana (balance RAM/CPU)
    OVERLAP_SEC = 30  # 30 segundos de solapamiento para continuidad

    def __init__(self, model_size: str = "tiny.en"):
        if whisper is None:
            raise EngineRuntimeError(
                "Las librerías 'whisper', 'librosa' o 'torch' no están instaladas."
            )

        self.model_size = model_size
        self._model = None  # Lazy loading

    def _load_model(self):
        """Carga el modelo en memoria solo cuando se necesita."""
        if self._model is None:
            try:
                # Forzamos CPU según requerimiento
                self._model = whisper.load_model(self.model_size, device="cpu")
            except Exception as e:
                raise EngineRuntimeError(f"Error cargando modelo Whisper: {e}") from e

    def detect_voice_activity(self, audio_path: Path) -> list[TimeRange]:
        """
        Implementa la estrategia de chunking deslizante para VAD.
        """
        if not audio_path.exists():
            raise AudioFileError(f"Archivo no encontrado: {audio_path}")

        self._load_model()

        # 1. Obtener duración total sin cargar el audio completo
        try:
            total_duration = librosa.get_duration(path=audio_path)
        except Exception as e:
            raise AudioFileError(f"No se pudo leer metadata del audio: {e}") from e

        raw_ranges: list[TimeRange] = []

        # 2. Iterar por ventanas (Chunking Strategy)
        # start va de 0 a total_duration, avanzando (CHUNK - OVERLAP)
        step = self.CHUNK_DURATION_SEC - self.OVERLAP_SEC

        current_start = 0.0
        while current_start < total_duration:
            # Calcular ventana actual
            duration_to_load = min(
                self.CHUNK_DURATION_SEC, total_duration - current_start
            )

            try:
                # Carga PARCIAL del audio (streaming desde disco -> RAM baja)
                # sr=16000 es obligatorio para Whisper
                audio_chunk, _ = librosa.load(
                    audio_path,
                    sr=16000,
                    offset=current_start,
                    duration=duration_to_load,
                )
            except Exception as e:
                raise EngineRuntimeError(
                    f"Error leyendo chunk {current_start}s: {e}"
                ) from e

            # 3. Inferencia (Transcribe)
            # fp16=False necesario en CPU
            try:

                # result = self._model.transcribe(
                # ✅ DESPUÉS
                result = self._model.transcribe(  [attr-defined]
                    audio_chunk, fp16=False, language="en", verbose=False
                )
            except RuntimeError as e:
                if "memory" in str(e).lower():
                    raise MemoryLimitExceeded(f"OOM durante inferencia: {e}") from e
                raise EngineRuntimeError(f"Fallo en inferencia Whisper: {e}") from e

            # 4. Mapeo de segmentos locales a globales
            for segment in result.get("segments", []):
                # Whisper a veces alucina timestamps fuera del rango del audio
                seg_start = segment["start"]
                seg_end = segment["end"]

                # Ajustar al tiempo global
                global_start = current_start + seg_start
                global_end = current_start + seg_end

                # Crear VO y añadir a la lista cruda
                # Validamos que no sean micro-alucinaciones (< 0.1s)
                if seg_end - seg_start > 0.1:
                    raw_ranges.append(
                        TimeRange(round(global_start, 2), round(global_end, 2))
                    )

            # Avanzar ventana
            current_start += step

            # Limpieza explícita de variables grandes
            del audio_chunk
            del result

        # 5. Reducción y Fusión (Merge Overlaps)
        return self._merge_overlapping_ranges(raw_ranges)

    def _merge_overlapping_ranges(self, ranges: list[TimeRange]) -> list[TimeRange]:
        """
        Fusiona rangos solapados o duplicados resultantes del chunking.
        Algoritmo O(N log N).
        """
        if not ranges:
            return []

        # Ordenar por inicio
        sorted_ranges = sorted(ranges, key=lambda r: r.start)
        merged = []

        current = sorted_ranges[0]

        for next_range in sorted_ranges[1:]:
            if current.overlaps_with(next_range) or current.end >= next_range.start:
                # Se solapan o tocan -> extender el actual
                # Usamos merge del VO (maneja max end)
                # Nota: TimeRange.merge puede lanzar error si están disjuntos,
                # pero aquí controlamos la condición.
                try:
                    current = current.merge(next_range)
                except ValueError:
                    # Si por flotantes fallara, simplemente cerramos current y abrimos next
                    merged.append(current)
                    current = next_range
            else:
                # No solapan -> guardar current y avanzar
                merged.append(current)
                current = next_range

        merged.append(current)
        return merged
