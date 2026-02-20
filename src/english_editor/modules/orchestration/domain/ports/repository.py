# src/english_editor/modules/orchestration/domain/ports/repository.py
"""
Puerto (Interface) para la persistencia de trabajos de procesamiento.

Arquitectura: Modular Monolith
Capa: Domain -> Ports
Responsabilidad: Abstraer el almacenamiento del estado (JSON, DB, Pickle).
"""

from abc import ABC, abstractmethod
from typing import Optional

# === Imports de Tipos de Dominio ===
from english_editor.modules.orchestration.domain.entities import ProcessingJob
from english_editor.modules.orchestration.domain.value_objects import SourceFingerprint


class JobRepository(ABC):
    """
    Contrato para guardar y recuperar el estado de los trabajos.
    Permite implementar la regla: 'Recuperación de Desastres (CE-01)'.
    """

    @abstractmethod
    def save(self, job: ProcessingJob) -> None:
        """
        Persiste el estado actual del job (incluyendo checkpoints).
        Debe ser atómico para evitar corrupciones.
        """
        pass

    @abstractmethod
    def find_last_by_fingerprint(
        self, fingerprint: SourceFingerprint
    ) -> Optional[ProcessingJob]:
        """
        Busca si existe un trabajo previo (inconcluso o terminado) para este archivo fuente exacto.
        Clave para la funcionalidad de 'Resume'.
        """
        pass
