# tests/modules/analysis/infrastructure/test_adapters.py
"""
Tests para: FakeSpeechEngine
Tipo: Unitario (Infrastructure)
"""

from pathlib import Path

import pytest

from english_editor.modules.analysis.domain.exceptions import AudioFileError
from english_editor.modules.analysis.domain.value_objects import TimeRange
from english_editor.modules.analysis.infrastructure.adapters import FakeSpeechEngine

# === Casos de Prueba ===


def test_fake_engine_returns_default_range():
    """
    Given: Un motor fake sin configuración especial
    When: Se analiza un archivo 'normal.wav'
    Then: Retorna el rango por defecto [0, 10]
    """
    # Arrange
    engine = FakeSpeechEngine()
    path = Path("normal.wav")

    # Act
    result = engine.detect_voice_activity(path)

    # Assert
    assert len(result) == 1
    assert result[0] == TimeRange(0.0, 10.0)


def test_fake_engine_simulates_silence():
    """
    Given: Un archivo con 'silence' en el nombre
    When: Se detecta actividad
    Then: Retorna lista vacía
    """
    # Arrange
    engine = FakeSpeechEngine()
    path = Path("long_silence.mp3")

    # Act
    result = engine.detect_voice_activity(path)

    # Assert
    assert result == []


def test_fake_engine_simulates_error():
    """
    Given: Un archivo con 'error' en el nombre
    When: Se intenta procesar
    Then: Lanza AudioFileError
    """
    # Arrange
    engine = FakeSpeechEngine()
    path = Path("corrupted_error.wav")

    # Act & Assert
    with pytest.raises(AudioFileError):
        engine.detect_voice_activity(path)


def test_fake_engine_respects_injected_result():
    """
    Given: Un motor configurado con resultado específico
    When: Se ejecuta
    Then: Retorna EXACTAMENTE ese resultado (ignorando el nombre del archivo)
    """
    # Arrange
    expected = [TimeRange(5.0, 15.0), TimeRange(20.0, 25.0)]
    engine = FakeSpeechEngine(fixed_result=expected)
    path = Path("whatever.wav")

    # Act
    result = engine.detect_voice_activity(path)

    # Assert
    assert result == expected
