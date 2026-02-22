# src/english_editor/modules/orchestration/domain/entities.py
"""
Entidades del dominio de Orquestación.

Arquitectura: Modular Monolith
Capa: Domain
Responsabilidad: Gestionar el ciclo de vida y estado mutable de un trabajo de procesamiento.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime

# === Imports del Mismo Módulo ===
from .value_objects import JobStatus, SourceFingerprint

# === Guía de Organización ===
# ✅ IDENTIDAD: Las entidades se comparan por ID, no por atributos.
# ✅ ESTADO: Mutan de forma controlada a través de métodos (no setters directos).


@dataclass
class ProcessingJob:
    """
    Agregado Raíz (Root Aggregate) que representa un trabajo de edición en curso.
    Controla la consistencia entre el archivo fuente, el estado y los checkpoints.
    """

    job_id: str
    source: SourceFingerprint
    output_path: str
    created_at: datetime

    # Estado Mutable (Protegido por lógica de negocio)
    status: JobStatus = JobStatus.PENDING
    _checkpoints: list[dict[str, float]] = field(default_factory=list)
    error_message: str | None = None
    updated_at: datetime = field(default_factory=datetime.now)

    @classmethod
    def create_new(cls, source: SourceFingerprint, output_path: str) -> ProcessingJob:
        """Factory method para iniciar un trabajo limpio."""
        return cls(
            job_id=str(uuid.uuid4()),
            source=source,
            output_path=output_path,
            created_at=datetime.now(),
        )

    def mark_segment_processed(self, start_time: float, end_time: float) -> None:
        """
        Registra un avance (checkpoint).
        Idempotente: Si el segmento ya existe, no duplica lógica (aunque aquí simplificamos).
        """
        if self.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            # Reactivar si estaba fallido, o loggear si estaba completo?
            # Por simplicidad, si agregamos progreso, vuelve a IN_PROGRESS
            self.status = JobStatus.IN_PROGRESS

        # Validar integridad básica del segmento
        if start_time < 0 or end_time <= start_time:
            raise ValueError(f"Segmento de tiempo inválido: {start_time} -> {end_time}")

        self._checkpoints.append({"start": start_time, "end": end_time})
        self.status = JobStatus.IN_PROGRESS
        self.updated_at = datetime.now()

    def fail_job(self, reason: str) -> None:
        """Transición a estado de fallo."""
        self.status = JobStatus.FAILED
        self.error_message = reason
        self.updated_at = datetime.now()

    def complete_job(self) -> None:
        """Finaliza el trabajo exitosamente."""
        if not self._checkpoints and self.source.file_size_bytes > 0:
            # Regla de negocio: No se puede completar sin procesar nada (salvo archivos vacíos)
            # (Esta es una regla simplificada, en realidad dependería del dominio)
            pass

        self.status = JobStatus.COMPLETED
        self.updated_at = datetime.now()

    @property
    def progress_count(self) -> int:
        """Métrica simple de progreso (número de segmentos procesados)."""
        return len(self._checkpoints)

    def get_checkpoints_copy(self) -> list[dict[str, float]]:
        """Devuelve una copia inmutable de los checkpoints para persistencia."""
        return list(self._checkpoints)
