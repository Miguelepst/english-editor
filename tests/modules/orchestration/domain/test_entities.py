# tests/modules/orchestration/domain/test_entities.py
"""
Tests unitarios para la Entidad ProcessingJob.
Foco: Transiciones de estado y protección de invariantes.
"""

import pytest

from english_editor.modules.orchestration.domain.entities import ProcessingJob
from english_editor.modules.orchestration.domain.value_objects import (
    JobStatus,
    SourceFingerprint,
)


# === Fixtures ===
@pytest.fixture
def sample_fingerprint():
    return SourceFingerprint(
        filename="test.mp4", file_size_bytes=1024, content_hash="dummy_hash"
    )


# === Casos de Prueba ===


def test_create_new_job_should_be_pending(sample_fingerprint):
    """
    Escenario: Creación de un nuevo trabajo.
    Resultado: Debe tener ID, estar en PENDING y sin checkpoints.
    """
    # Act
    job = ProcessingJob.create_new(sample_fingerprint, "/out/path")

    # Assert
    assert job.status == JobStatus.PENDING
    assert job.job_id is not None
    assert job.progress_count == 0


def test_mark_segment_should_advance_status(sample_fingerprint):
    """
    Escenario: Se registra el primer segmento procesado.
    Resultado: El estado cambia a IN_PROGRESS y aumenta el contador.
    """
    # Arrange
    job = ProcessingJob.create_new(sample_fingerprint, "/out/path")

    # Act
    job.mark_segment_processed(0.0, 10.0)

    # Assert
    assert job.status == JobStatus.IN_PROGRESS
    assert job.progress_count == 1
    # Verificar que el checkpoint se guardó correctamente
    checkpoints = job.get_checkpoints_copy()
    assert checkpoints[0] == {"start": 0.0, "end": 10.0}


def test_fail_job_should_record_reason(sample_fingerprint):
    # Arrange
    job = ProcessingJob.create_new(sample_fingerprint, "/out/path")

    # Act
    job.fail_job("Disk full")

    # Assert
    assert job.status == JobStatus.FAILED
    assert job.error_message == "Disk full"


def test_invalid_segment_should_raise_error(sample_fingerprint):
    """
    Regla: No permitir segmentos con tiempo negativo o final < inicio.
    """
    # Arrange
    job = ProcessingJob.create_new(sample_fingerprint, "/out/path")

    # Act & Assert
    with pytest.raises(ValueError):
        job.mark_segment_processed(10.0, 5.0)  # End antes que Start
