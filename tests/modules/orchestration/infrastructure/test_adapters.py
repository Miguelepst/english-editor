# tests/modules/orchestration/infrastructure/test_adapters.py
"""
Tests de Integración para Adaptadores de Infraestructura.
Requieren acceso a disco (usamos tmp_path).
"""

import json

from english_editor.modules.orchestration.domain.entities import ProcessingJob
from english_editor.modules.orchestration.domain.value_objects import SourceFingerprint
from english_editor.modules.orchestration.infrastructure.adapters import (
    JsonFileRepository,
    LocalFileSystemAdapter,
)

# === Tests para JsonFileRepository ===


def test_repository_save_and_retrieve(tmp_path):
    """
    Escenario: Guardar un Job en un archivo JSON nuevo y recuperarlo.
    """
    # Arrange
    db_file = tmp_path / "jobs_db.json"
    repo = JsonFileRepository(str(db_file))

    fingerprint = SourceFingerprint("video.mp4", 1024, "hash_unique_123")
    job = ProcessingJob.create_new(fingerprint, "/out/video_editado.mp4")
    job.mark_segment_processed(0, 10)

    # Act
    repo.save(job)
    retrieved_job = repo.find_last_by_fingerprint(fingerprint)

    # Assert
    assert retrieved_job is not None
    assert retrieved_job.job_id == job.job_id
    assert retrieved_job.progress_count == 1
    assert retrieved_job.get_checkpoints_copy()[0]["end"] == 10.0

    # Verificar que el archivo existe físicamente
    with open(db_file) as f:
        content = json.load(f)
        assert "hash_unique_123" in content["jobs"]


def test_repository_returns_none_if_missing(tmp_path):
    # Arrange
    db_file = tmp_path / "empty_db.json"
    repo = JsonFileRepository(str(db_file))
    fingerprint = SourceFingerprint("missing.mp4", 10, "hash_missing")

    # Act
    result = repo.find_last_by_fingerprint(fingerprint)

    # Assert
    assert result is None


# === Tests para LocalFileSystemAdapter ===


def test_fs_smart_hash_consistency(tmp_path):
    """
    Escenario: Calcular hash de un archivo dos veces debe dar lo mismo.
    Cambiar contenido debe cambiar hash.
    """
    # Arrange
    fs = LocalFileSystemAdapter()
    file_path = tmp_path / "test_video.mp4"

    # Crear archivo dummy
    with open(file_path, "wb") as f:
        f.write(b"content_A" * 1000)

    # Act
    fp1 = fs.calculate_fingerprint(str(file_path))
    fp2 = fs.calculate_fingerprint(str(file_path))

    # Modificar archivo
    with open(file_path, "wb") as f:
        f.write(b"content_B" * 1000)
    fp3 = fs.calculate_fingerprint(str(file_path))

    # Assert
    assert fp1 == fp2
    assert fp1.content_hash != fp3.content_hash
    assert (
        fp1.file_size_bytes == fp3.file_size_bytes
    )  # Mismo tamaño, diferente contenido
