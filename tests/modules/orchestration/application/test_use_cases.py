from datetime import datetime
from unittest.mock import Mock

import pytest

from english_editor.modules.orchestration.application.use_cases import JobOrchestrator
from english_editor.modules.orchestration.domain.entities import ProcessingJob
from english_editor.modules.orchestration.domain.value_objects import (
    JobStatus,
    SourceFingerprint,
)


@pytest.fixture
def mock_repo():
    return Mock()


@pytest.fixture
def mock_fs():
    fs = Mock()
    fs.exists.return_value = False
    fs.list_files.return_value = []

    def fake_fingerprint(path):
        return SourceFingerprint("dummy", 100, "hash_" + path)

    fs.calculate_fingerprint.side_effect = fake_fingerprint
    return fs


@pytest.fixture
def orchestrator(mock_repo, mock_fs):
    return JobOrchestrator(mock_repo, mock_fs)


def test_prepare_jobs_creates_new(orchestrator, mock_fs, mock_repo):
    input_file = "video1.mp4"
    mock_fs.exists.return_value = False
    mock_repo.find_last_by_fingerprint.return_value = None

    jobs = list(orchestrator.prepare_jobs(input_file, "/out"))
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.PENDING


def test_resume_existing_job(orchestrator, mock_fs, mock_repo):
    """
    Verifica que si existe un job previo, se retoma.
    """
    input_file = "video1.mp4"
    mock_fs.exists.return_value = False
    fingerprint = SourceFingerprint("video1.mp4", 1024, "hash123")

    # === AQUÍ ESTABA EL ERROR ANTERIOR ===
    # Ahora usamos los nombres correctos de tu nueva entidad
    real_job = ProcessingJob(
        job_id="uuid-real-123",
        source=fingerprint,  # ✅ source (no source_fingerprint)
        output_path="/out/res.mp4",  # ✅ output_path (no expected_output)
        created_at=datetime.now(),  # ✅ created_at (obligatorio)
    )
    real_job.status = JobStatus.FAILED

    mock_repo.find_last_by_fingerprint.return_value = real_job

    jobs = list(orchestrator.prepare_jobs(input_file, "/out"))

    assert len(jobs) == 1
    assert jobs[0].job_id == "uuid-real-123"
    assert jobs[0].status == JobStatus.FAILED
