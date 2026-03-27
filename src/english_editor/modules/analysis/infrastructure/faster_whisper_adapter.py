
# @title 📄 faster_whisper_adapter.py — [Infrastructure Adapter] Adaptador de infraestructura SRE para Faster-Whisper

# ✅ Archivo creado: /content/english-editor/src/english_editor/modules/analysis/infrastructure/faster_whisper_adapter.py
# 📦 Repo GitHub:    'english-editor'  (kebab-case → github.com/.../english-editor)
# 📦 Paquete Python: 'english_editor'  (snake_case → imports: from english_editor.modules...)
# 💡 Import válido: from english_editor.modules.analysis.infrastructure.faster_whisper_adapter import FasterWhisperAdapter

# src/english_editor/modules/analysis/infrastructure/faster_whisper_adapter.py
"""
Adaptador de infraestructura SRE para Faster-Whisper.

Arquitectura: Modular Monolith + Vertical Slice
Componente: Infrastructure Adapter
Responsabilidad: Implementar SpeechAnalysisEngine usando el motor optimizado CTranslate2 (faster-whisper).
"""

from __future__ import annotations

# === 🧭 Protocolos Arquitectónicos (Strict Layering) ===
# ✅ CORE: Building blocks universales (value objects, tipos básicos)
# ✅ MODULES: Bounded contexts verticales y aislados
# ❌ DOMAIN → APPLICATION/INFRA: Prohibido (rompe Clean Architecture)
# ❌ MODULES → MODULES: Prohibido (comunicación solo vía Core o Puertos)
# ✅ INFRASTRUCTURE: Solo adaptadores concretos (nunca lógica de negocio)
# === 🧪 Protocolos de Calidad Obligatorios ===
# 🔒 Inmutabilidad: Value Objects → @dataclass(frozen=True)
# 🧪 Testabilidad: Componente debe ser testeable SIN mocks de infraestructura
# 🔤 Type Hints: Firmas públicas con type hints explícitos (PEP 484)
# ⚡ Pureza: Funciones puras donde sea posible (misma entrada → misma salida)
# 🚫 Excepciones específicas: Define excepciones de dominio (no uses Exception genérico)
# 📏 Longitud de línea: Máximo 88 caracteres (compatible con Black/Ruff)
# === Imports estándar ===
from pathlib import Path

# === Imports de terceros (Fallback SRE) ===
try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

# === Imports del proyecto ===
from english_editor.modules.analysis.domain.exceptions import (
    AudioFileError,
    EngineRuntimeError,
    MemoryLimitExceeded,
)
from english_editor.modules.analysis.domain.value_objects import TimeRange


# === Definición principal ===
class FasterWhisperAdapter:
    """
    Implementación SRE usando 'faster-whisper' (CTranslate2).
    A diferencia del adaptador original, este motor maneja la memoria nativamente
    sin necesidad de chunking manual con librosa, y utiliza el filtro VAD interno.
    """

    def __init__(
        self,
        model_size: str = "tiny.en",
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        if WhisperModel is None:
            raise EngineRuntimeError("La librería 'faster-whisper' no está instalada.")

        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None

    def _load_model(self) -> None:
        """Carga el modelo en memoria RAM solo cuando se necesita (Lazy Loading)."""
        if self._model is None:
            try:
                self._model = WhisperModel(
                    self.model_size, device=self.device, compute_type=self.compute_type
                )
            except Exception as e:
                raise EngineRuntimeError(
                    f"Error cargando modelo Faster-Whisper: {e}"
                ) from e

    def detect_voice_activity(self, audio_path: Path) -> list[TimeRange]:
        """
        Analiza el audio usando VAD y Word-level Timestamps para precisión estricta.
        Cumple con el contrato devolviendo list[TimeRange] en milisegundos.
        """
        if not audio_path.exists():
            raise AudioFileError(f"Archivo no encontrado: {audio_path}")

        self._load_model()
        raw_ranges: list[TimeRange] = []

        try:
            # vad_filter salta silencios largos. word_timestamps evita estiramientos.
            segments_generator, info = self._model.transcribe(
                str(audio_path), beam_size=5, vad_filter=True, word_timestamps=True
            )

            for segment in segments_generator:
                if segment.words:
                    start_sec = segment.words[0].start
                    end_sec = segment.words[-1].end
                else:
                    start_sec = segment.start
                    end_sec = segment.end

                # Validamos micro-alucinaciones (< 0.1s)
                if end_sec - start_sec > 0.1:
                    raw_ranges.append(
                        TimeRange(
                            round(start_sec * 1000.0, 2), round(end_sec * 1000.0, 2)
                        )
                    )

        except Exception as e:
            if "memory" in str(e).lower() or "alloc" in str(e).lower():
                raise MemoryLimitExceeded(f"OOM en CTranslate2: {e}") from e
            raise EngineRuntimeError(f"Fallo en inferencia Faster-Whisper: {e}") from e

        return self._merge_overlapping_ranges(raw_ranges)

    def _merge_overlapping_ranges(self, ranges: list[TimeRange]) -> list[TimeRange]:
        """
        Fusiona rangos solapados resultantes del análisis.
        Algoritmo O(N log N).
        """
        if not ranges:
            return []

        sorted_ranges = sorted(ranges, key=lambda r: r.start)
        merged: list[TimeRange] = []
        current = sorted_ranges[0]

        for next_range in sorted_ranges[1:]:
            if current.overlaps_with(next_range) or current.end >= next_range.start:
                try:
                    current = current.merge(next_range)
                except ValueError:
                    merged.append(current)
                    current = next_range
            else:
                merged.append(current)
                current = next_range

        merged.append(current)
        return merged


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    # ⚠️ Evita lógica de negocio aquí. Usa tests/ para validación.
    # ✅ Solo para demos controladas o scripts utilitarios.
    pass









