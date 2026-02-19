# tests/modules/analysis/application/test_use_cases.py
"""
Tests para: AnalyzeAudio (Use Case)
Tipo: Unitario (Application)
"""
import pytest
from pathlib import Path
from unittest.mock import Mock

from english_editor.modules.analysis.application.use_cases import AnalyzeAudio
from english_editor.modules.analysis.infrastructure.adapters import FakeSpeechEngine
from english_editor.modules.analysis.domain.value_objects import TimeRange
from english_editor.modules.analysis.domain.exceptions import AudioFileError

# === Fixtures ===

@pytest.fixture
def fake_engine():
    """Retorna un motor fake limpio para cada test."""
    return FakeSpeechEngine()

@pytest.fixture
def use_case(fake_engine):
    """Inyecta el motor fake en el caso de uso."""
    return AnalyzeAudio(engine=fake_engine)

# === Casos de Prueba ===

def test_analyze_audio_success(use_case, tmp_path):
    """
    Given: Un archivo de audio válido
    When: Se ejecuta el caso de uso
    Then: Retorna los segmentos detectados por el motor
    """
    # Arrange
    # Creamos un archivo dummy para pasar la validación de .exists()
    audio_file = tmp_path / "interview.mp3"
    audio_file.touch()

    # Act
    result = use_case.execute(audio_file)

    # Assert
    # El Fake por defecto devuelve [0, 10]
    assert len(result) == 1
    assert result[0] == TimeRange(0.0, 10.0)

def test_analyze_audio_fails_if_file_missing(use_case):
    """
    Given: Una ruta a un archivo inexistente
    When: Se ejecuta el caso de uso
    Then: Lanza AudioFileError (Fail Fast)
    """
    # Arrange
    missing_file = Path("ghost_file.wav")

    # Act & Assert
    with pytest.raises(AudioFileError) as exc:
        use_case.execute(missing_file)

    assert "no existe" in str(exc.value).lower()

def test_analyze_audio_propagates_engine_errors(use_case, tmp_path):
    """
    Given: Un archivo que provoca error en el motor (simulado con 'error' en nombre)
    When: Se ejecuta el caso de uso
    Then: La excepción sube hasta el caller
    """
    # Arrange
    corrupted_file = tmp_path / "corrupted_error.wav"
    corrupted_file.touch()

    # Act & Assert
    with pytest.raises(AudioFileError):
        use_case.execute(corrupted_file)

def test_analyze_audio_with_fixed_result(tmp_path):
    """
    Given: Un motor configurado con respuesta fija
    When: Se ejecuta el caso de uso
    Then: Retorna exactamente esa respuesta
    """
    # Arrange
    expected = [TimeRange(1.0, 2.0)]
    # Inyección manual sin fixture para este caso específico
    engine = FakeSpeechEngine(fixed_result=expected)
    use_case = AnalyzeAudio(engine)

    audio_file = tmp_path / "test.wav"
    audio_file.touch()

    # Act
    result = use_case.execute(audio_file)

    # Assert
    assert result == expected