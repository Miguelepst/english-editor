
# @title 🧪 test_faster_whisper_adapter.py — [Test] Tests para el adaptador SRE de Faster-Whisper

# ✅ Test creado: /content/english-editor/tests/modules/analysis/infrastructure/test_faster_whisper_adapter.py
# 📦 Repo GitHub:    'english-editor'  (kebab-case → github.com/.../english-editor)
# 📦 Paquete Python: 'english_editor'  (snake_case → imports: from english_editor.modules...)
# 🧪 Ejecutar test: cd /content/english-editor && python -m pytest tests/modules/analysis/infrastructure/test_faster_whisper_adapter.py -v
# 💡 Protocolo clave: Usamos @patch para evitar descargar o cargar el modelo real en los tests.

# tests/modules/analysis/infrastructure/test_faster_whisper_adapter.py
"""
Tests para: faster_whisper_adapter.py
Tipo: Unitario (Infraestructura Mockeada)
Arquitectura: AAA (Arrange-Act-Assert) + Given-When-Then
Protocolos: Pureza de dominio, Aislamiento, Determinismo
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# === 🧪 Protocolos de Calidad Obligatorios ===
# 🔒 DOMINIO PURO: Tests sin I/O ni mocks. Solo lógica de negocio.
# 🧪 AISLAMIENTO: Cada test es independiente (no comparte estado con otros tests).
# ⚡ VELOCIDAD: Tests unitarios < 100ms. Tests lentos marcar con @pytest.mark.slow.
# 🔤 DETERMINISMO: Sin aleatoriedad sin seed controlado.
# 🚫 SIN EFECTOS SECUNDARIOS: Nunca escribir en filesystem real (usar tmp_path fixture).
# 🌐 SIN DEPENDENCIAS EXTERNAS: Mockear APIs, redes, bases de datos en tests unitarios.
# === Imports del SUT (System Under Test) ===
from english_editor.modules.analysis.domain.exceptions import (
    AudioFileError,
    EngineRuntimeError,
    MemoryLimitExceeded,
)
from english_editor.modules.analysis.domain.value_objects import TimeRange
from english_editor.modules.analysis.infrastructure.faster_whisper_adapter import (
    FasterWhisperAdapter,
)

# === Casos de Prueba ===


@patch(
    "english_editor.modules.analysis.infrastructure.faster_whisper_adapter.WhisperModel"
)
def test_detect_voice_activity_should_raise_audiofileerror_when_file_missing(
    mock_whisper_class,
):
    """
    Given: Una ruta a un archivo de audio que no existe físicamente.
    When:  Se intenta detectar actividad de voz.
    Then:  El sistema debe lanzar un AudioFileError inmediatamente (Fail-Fast).
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    adapter = FasterWhisperAdapter()
    fake_path = Path("/ruta/inventada/que/no/existe.mp4")

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    with pytest.raises(AudioFileError) as exc_info:
        adapter.detect_voice_activity(fake_path)

    assert "Archivo no encontrado" in str(exc_info.value), (
        "Debe especificar que el archivo falta"
    )


@patch(
    "english_editor.modules.analysis.infrastructure.faster_whisper_adapter.WhisperModel"
)
def test_detect_voice_activity_should_return_milliseconds_mapped_from_words(
    mock_whisper_class, tmp_path
):
    """
    Given: Un archivo de audio válido y un motor Whisper que detecta palabras.
    When:  Se transcribe el audio.
    Then:  El adaptador debe mapear los segundos de las palabras a milisegundos en el VO TimeRange.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    # Creamos un archivo falso seguro para que pase la validación de Path.exists()
    dummy_audio = tmp_path / "test_audio.mp4"
    dummy_audio.touch()

    adapter = FasterWhisperAdapter()

    # Configuramos el Mock de Faster-Whisper para devolver un generador controlado
    mock_model_instance = mock_whisper_class.return_value

    # Simulamos el objeto 'Word' que devuelve CTranslate2
    word1 = MagicMock(start=1.5, end=2.0)
    word2 = MagicMock(start=2.0, end=3.5)

    # Simulamos el objeto 'Segment'
    mock_segment = MagicMock()
    mock_segment.words = [word1, word2]

    # El método transcribe devuelve una tupla (generador_segmentos, info_diccionario)
    mock_model_instance.transcribe.return_value = ([mock_segment], {"language": "en"})

    # ─── ACT ────────────────────────────────────────────────────────────────────
    result = adapter.detect_voice_activity(dummy_audio)

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert len(result) == 1, "Debe retornar exactamente 1 TimeRange"

    # 1.5s -> 1500.0ms | 3.5s -> 3500.0ms (Contrato del Dominio)
    assert result[0].start == 1500.0, "El inicio debe estar convertido a milisegundos"
    assert result[0].end == 3500.0, "El fin debe estar convertido a milisegundos"

    # Verificar que llamamos a la librería con los parámetros SRE obligatorios
    mock_model_instance.transcribe.assert_called_once_with(
        str(dummy_audio), beam_size=5, vad_filter=True, word_timestamps=True
    )


@patch(
    "english_editor.modules.analysis.infrastructure.faster_whisper_adapter.WhisperModel"
)
def test_detect_voice_activity_should_translate_oom_to_domain_exception(
    mock_whisper_class, tmp_path
):
    """
    Given: Un entorno de ejecución que se queda sin RAM durante la inferencia.
    When:  El motor CTranslate2 lanza un RuntimeError de memoria.
    Then:  El adaptador debe traducirlo a la excepción de dominio MemoryLimitExceeded.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    dummy_audio = tmp_path / "test_oom.mp4"
    dummy_audio.touch()

    adapter = FasterWhisperAdapter()
    mock_model_instance = mock_whisper_class.return_value

    # Simulamos un colapso de hardware de la librería de C++
    mock_model_instance.transcribe.side_effect = RuntimeError(
        "Failed to allocate memory"
    )

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    with pytest.raises(MemoryLimitExceeded) as exc_info:
        adapter.detect_voice_activity(dummy_audio)

    assert "OOM en CTranslate2" in str(exc_info.value), (
        "Debe etiquetar claramente el error como OOM"
    )


@patch(
    "english_editor.modules.analysis.infrastructure.faster_whisper_adapter.WhisperModel"
)
def test_merge_overlapping_ranges_should_combine_touching_ranges(mock_whisper_class):
    """
    Given: Una lista cruda de TimeRanges que se tocan o solapan.
    When:  El adaptador ejecuta su método interno de fusión.
    Then:  Debe devolver una lista limpia de rangos contiguos.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    adapter = FasterWhisperAdapter()
    raw_ranges = [
        TimeRange(0.0, 5000.0),  # Rango 1
        TimeRange(4500.0, 8000.0),  # Rango 2 (solapa con 1)
        TimeRange(8000.0, 10000.0),  # Rango 3 (toca el fin de 2)
        TimeRange(15000.0, 20000.0),  # Rango 4 (aislado)
    ]

    # ─── ACT ────────────────────────────────────────────────────────────────────
    # Invocamos el método privado explícitamente para testear su algoritmo O(N log N)
    merged_result = adapter._merge_overlapping_ranges(raw_ranges)

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert len(merged_result) == 2, (
        "Debe reducir los 4 rangos iniciales a 2 bloques consolidados"
    )

    # Bloque 1 (Fusión del 1, 2 y 3)
    assert merged_result[0].start == 0.0
    assert merged_result[0].end == 10000.0

    # Bloque 2 (Aislado)
    assert merged_result[1].start == 15000.0
    assert merged_result[1].end == 20000.0


