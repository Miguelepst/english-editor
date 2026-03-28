
# @title 🧪 test_whisper_adapter.py — [Test] Corregido (Aislamiento Total)

# ✅ Test de infraestructura actualizado: /content/english-editor/tests/modules/analysis/infrastructure/test_whisper_adapter.py

# tests/modules/analysis/infrastructure/test_whisper_adapter.py
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from english_editor.modules.analysis.domain.exceptions import (
    AudioFileError,
    EngineRuntimeError,
    MemoryLimitExceeded,
)
from english_editor.modules.analysis.infrastructure.whisper_adapter import (
    WhisperLocalAdapter,
)

# --- MOCKS GLOBALES PARA LA SUITE ---
# Definimos el string del patch para no repetirlo
MOCK_WHISPER = "english_editor.modules.analysis.infrastructure.whisper_adapter.whisper"
MOCK_LIBROSA = "english_editor.modules.analysis.infrastructure.whisper_adapter.librosa"

# ==============================================================================


# ✅ CORRECCIÓN: Agregamos el parche de whisper para que sobreviva al __init__
@patch(MOCK_WHISPER)
def test_detect_voice_activity_should_raise_audiofileerror_when_file_missing(
    mock_whisper,
):
    """Falla rápido lanzando AudioFileError sin cargar el modelo."""
    adapter = WhisperLocalAdapter()
    fake_path = Path("/ruta/fantasma/audio.mp4")

    with pytest.raises(AudioFileError) as exc_info:
        adapter.detect_voice_activity(fake_path)

    assert "Archivo no encontrado" in str(exc_info.value)


@patch(MOCK_LIBROSA)
@patch(MOCK_WHISPER)
def test_detect_voice_activity_should_extract_exact_word_timestamps(
    mock_whisper, mock_librosa, tmp_path
):
    """El adaptador debe ignorar el tiempo del segmento y usar estrictamente palabras."""
    dummy_audio = tmp_path / "test_words.mp4"
    dummy_audio.touch()

    adapter = WhisperLocalAdapter()
    mock_librosa.get_duration.return_value = 10.0
    mock_librosa.load.return_value = ([0.1, 0.2], 16000)

    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model

    mock_model.transcribe.return_value = {
        "segments": [
            {
                "start": 0.0,
                "end": 5.0,
                "words": [
                    {"start": 1.5, "end": 2.0, "word": "Hello"},
                    {"start": 2.5, "end": 3.5, "word": "World"},
                ],
            }
        ]
    }

    result = adapter.detect_voice_activity(dummy_audio)

    assert len(result) == 1
    assert result[0].start == 1500.0
    assert result[0].end == 3500.0


@patch(MOCK_LIBROSA)
@patch(MOCK_WHISPER)
def test_detect_voice_activity_should_fallback_to_segment_when_words_missing(
    mock_whisper, mock_librosa, tmp_path
):
    """El adaptador debe ser resiliente y usar el tiempo general del segmento."""
    dummy_audio = tmp_path / "test_fallback.mp4"
    dummy_audio.touch()

    adapter = WhisperLocalAdapter()
    mock_librosa.get_duration.return_value = 10.0
    mock_librosa.load.return_value = ([0.1, 0.2], 16000)

    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_model.transcribe.return_value = {"segments": [{"start": 2.0, "end": 8.0}]}

    result = adapter.detect_voice_activity(dummy_audio)

    assert len(result) == 1
    assert result[0].start == 2000.0
    assert result[0].end == 8000.0


@patch(MOCK_LIBROSA)
@patch(MOCK_WHISPER)
def test_detect_voice_activity_should_catch_librosa_oom(
    mock_whisper, mock_librosa, tmp_path
):
    """El adaptador debe traducir errores de memoria a MemoryLimitExceeded."""
    dummy_audio = tmp_path / "test_oom.mp4"
    dummy_audio.touch()

    adapter = WhisperLocalAdapter()
    mock_librosa.get_duration.return_value = 600.0
    mock_librosa.load.return_value = ([0.1], 16000)

    mock_model = MagicMock()
    mock_whisper.load_model.return_value = mock_model
    mock_model.transcribe.side_effect = RuntimeError("memory error")

    with pytest.raises(MemoryLimitExceeded) as exc_info:
        adapter.detect_voice_activity(dummy_audio)

    assert "OOM durante inferencia" in str(exc_info.value)


