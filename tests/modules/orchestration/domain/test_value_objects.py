# tests/modules/orchestration/domain/test_value_objects.py
"""
Tests para Value Objects de Orquestación.
Enfoque: Validar reglas de integridad y comparación.
"""

import pytest

from english_editor.modules.orchestration.domain.value_objects import (
    JobStatus,
    SourceFingerprint,
)

# === Casos de Prueba para SourceFingerprint ===


def test_fingerprint_should_detect_corruption_same_filename():
    """
    Regla: Integridad de Fuente (DR-05).
    Escenario: Mismo nombre de archivo, pero diferente contenido (hash/size).
    Resultado: No deben ser considerados iguales.
    """
    # Arrange
    original = SourceFingerprint(
        filename="video.mp4", file_size_bytes=1000, content_hash="abc123hash"
    )
    corrupted = SourceFingerprint(
        filename="video.mp4", file_size_bytes=999, content_hash="xyz987hash"
    )

    # Act & Assert
    assert not original.matches(
        corrupted
    ), "Debe detectar cambio de contenido aunque el nombre sea igual"
    assert original != corrupted


def test_fingerprint_should_recognize_renamed_file():
    """
    Escenario: El archivo fue renombrado, pero el contenido es idéntico.
    Resultado: Debe reconocerse como el mismo activo (útil para deduplicación).
    """
    # Arrange
    file_a = SourceFingerprint(
        filename="video_v1.mp4", file_size_bytes=500, content_hash="unique_hash"
    )
    file_b = SourceFingerprint(
        filename="video_final.mp4", file_size_bytes=500, content_hash="unique_hash"
    )

    # Act & Assert
    assert file_a.matches(
        file_b
    ), "Debe identificar que es el mismo contenido subyacente"


def test_fingerprint_validation_rules():
    """
    Valida que no se puedan crear huellas invalidas.
    """
    # Assert
    with pytest.raises(ValueError):
        SourceFingerprint(filename="", file_size_bytes=10, content_hash="h")

    with pytest.raises(ValueError):
        SourceFingerprint(filename="a", file_size_bytes=-1, content_hash="h")


# === Casos de Prueba para JobStatus ===


def test_job_status_logic():
    # Arrange
    completed = JobStatus.COMPLETED
    in_progress = JobStatus.IN_PROGRESS

    # Assert
    assert completed.is_terminal() is True
    assert in_progress.is_terminal() is False
    assert in_progress.can_resume() is True
