
# @title 🧪 test_exceptions.py — [Test] Domain Exceptions
# ✅ Test creado: /content/english-editor/tests/modules/analysis/domain/test_exceptions.py
# tests/modules/analysis/domain/test_exceptions.py
"""
Tests para: Domain Exceptions
Tipo: Unitario (Domain)
"""

import pytest

from english_editor.modules.analysis.domain.exceptions import (
    AnalysisError,
    AudioFileError,
    EngineRuntimeError,
    MemoryLimitExceeded,
)

# === Casos de Prueba ===


def test_analysis_error_is_exception():
    """
    Given: La clase base AnalysisError
    When: Se evalúa su herencia
    Then: Debe heredar de Exception
    """
    assert issubclass(AnalysisError, Exception)


def test_audio_file_error_inherits_analysis_error():
    """
    Given: AudioFileError
    When: Se evalúa su jerarquía
    Then: Debe heredar de AnalysisError
    """
    assert issubclass(AudioFileError, AnalysisError)


def test_engine_runtime_error_inherits_analysis_error():
    """
    Given: EngineRuntimeError
    When: Se evalúa su jerarquía
    Then: Debe heredar de AnalysisError
    """
    assert issubclass(EngineRuntimeError, AnalysisError)


def test_memory_limit_exceeded_inherits_engine_runtime_error():
    """
    Given: MemoryLimitExceeded
    When: Se evalúa su jerarquía
    Then: Debe heredar de EngineRuntimeError
    """
    assert issubclass(MemoryLimitExceeded, EngineRuntimeError)


def test_audio_file_error_can_be_raised():
    """
    Given: Un error de archivo de audio
    When: Se lanza la excepción
    Then: Debe ser capturada correctamente
    """
    with pytest.raises(AudioFileError) as exc_info:
        raise AudioFileError("Archivo inválido")

    assert "archivo inválido" in str(exc_info.value).lower()


def test_memory_limit_exceeded_can_be_raised_as_engine_error():
    """
    Given: MemoryLimitExceeded
    When: Se lanza la excepción
    Then: Debe ser capturada como EngineRuntimeError
    """
    with pytest.raises(EngineRuntimeError):
        raise MemoryLimitExceeded("OOM")


def test_exception_polymorphism():
    """
    Given: Una excepción específica
    When: Se captura como clase base
    Then: Debe respetar el polimorfismo
    """
    try:
        raise MemoryLimitExceeded("OOM")
    except AnalysisError as e:
        assert isinstance(e, MemoryLimitExceeded)

