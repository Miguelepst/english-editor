# tests/e2e/test_orchestrator_e2e.py
"""
Tests End-to-End (E2E) para el subsistema de Orquestación.
Objetivo: Validar comportamiento con archivos de gran tamaño y ciclos de vida completos.
"""

import os

# import pytest
import shutil
import time

from english_editor.modules.orchestration.application.use_cases import JobOrchestrator
from english_editor.modules.orchestration.domain.value_objects import JobStatus
from english_editor.modules.orchestration.infrastructure.adapters import (
    JsonFileRepository,
    LocalFileSystemAdapter,
)

# === Escenarios E2E ===


def test_performance_on_huge_files(tmp_path, big_file_factory):
    """
    Escenario: Procesar un archivo de 5GB.
    Validación: El cálculo del hash (identidad) debe ser casi instantáneo (< 1s),
    demostrando que NO estamos leyendo los 5GB enteros.
    """
    # Arrange
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    os.makedirs(input_dir)
    os.makedirs(output_dir)

    # Crear un archivo de 5GB (falso/sparse)
    huge_file = big_file_factory("movie_4k_5gb.mp4", size_gb=5.0)
    # Moverlo al input dir (shutil.move preserva sparse en sistemas modernos, o copia rápido)
    final_path = os.path.join(input_dir, "movie_4k_5gb.mp4")
    shutil.move(huge_file, final_path)

    repo = JsonFileRepository(str(tmp_path / "db.json"))
    fs = LocalFileSystemAdapter()
    orchestrator = JobOrchestrator(repo, fs)

    # Act
    start_time = time.time()
    jobs = list(orchestrator.prepare_jobs(str(input_dir), str(output_dir)))
    duration = time.time() - start_time

    # Assert
    assert len(jobs) == 1
    # IMPORTANTE: Si lee todo el archivo, tardaría >10s. Si tarda <1s, la optimización funciona.
    print(f"\n⏱️ Tiempo de procesamiento para 5GB: {duration:.4f}s")
    assert duration < 1.0, (
        "El sistema es demasiado lento, parece estar leyendo el archivo completo."
    )
    assert (
        jobs[0].source.file_size_bytes > 5 * 10**9
    )  # Confirmar que detecta el tamaño correcto


def test_integrity_check_tail_mutation(tmp_path, big_file_factory):
    """
    Escenario: Integridad de Fuente (DR-05) en archivos grandes.
    Si cambio un byte al FINAL de un archivo gigante, el sistema debe darse cuenta.
    Esto valida que el SmartHash está leyendo el final del archivo.
    """
    # Arrange
    input_dir = tmp_path / "inputs"
    os.makedirs(input_dir)
    # repo = JsonFileRepository(str(tmp_path / "db.json"))
    fs = LocalFileSystemAdapter()

    # 1. Crear archivo original
    file_path = big_file_factory("video_large.mp4", size_gb=1.0)  # 1GB
    shutil.move(file_path, os.path.join(input_dir, "video_large.mp4"))
    full_path = os.path.join(input_dir, "video_large.mp4")

    # 2. Calcular fingerprint original
    fp_original = fs.calculate_fingerprint(full_path)

    # Act - Modificar el archivo al final (byte change)
    with open(full_path, "r+b") as f:
        f.seek(-1, os.SEEK_END)  # Ir al último byte
        f.write(b"X")  # Cambiarlo

    # Calcular nuevo fingerprint
    fp_modified = fs.calculate_fingerprint(full_path)

    # Assert
    assert fp_original.file_size_bytes == fp_modified.file_size_bytes
    assert fp_original.content_hash != fp_modified.content_hash, (
        "El hash no cambió tras modificar el final del archivo. ¿Estamos leyendo la cola?"
    )


def test_full_lifecycle_crash_recovery(tmp_path):
    """
    Escenario: Ciclo completo -> Inicio -> Progreso -> Reinicio -> Continuación.
    """
    # Arrange
    input_dir = tmp_path / "inputs"
    output_dir = tmp_path / "outputs"
    os.makedirs(input_dir)
    os.makedirs(output_dir)
    db_path = str(tmp_path / "checkpoint.json")

    # Crear archivo dummy normal
    with open(input_dir / "class.mp4", "wb") as f:
        f.write(b"content" * 100)

    repo = JsonFileRepository(db_path)
    fs = LocalFileSystemAdapter()
    orchestrator = JobOrchestrator(repo, fs)

    # --- FASE 1: Primer Run ---
    jobs_run1 = list(orchestrator.prepare_jobs(str(input_dir), str(output_dir)))
    job = jobs_run1[0]

    # Simular trabajo (Checkpoint)
    job.mark_segment_processed(0, 60)
    repo.save(job)

    # --- FASE 2: Reinicio (Nueva instancia de todo) ---
    repo_2 = JsonFileRepository(db_path)  # Carga desde disco
    orchestrator_2 = JobOrchestrator(repo_2, fs)

    jobs_run2 = list(orchestrator_2.prepare_jobs(str(input_dir), str(output_dir)))
    restored_job = jobs_run2[0]

    # Assert
    assert restored_job.job_id == job.job_id
    assert restored_job.status == JobStatus.IN_PROGRESS
    assert restored_job.get_checkpoints_copy() == [{"start": 0, "end": 60}]
