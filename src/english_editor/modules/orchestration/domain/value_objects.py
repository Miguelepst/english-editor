# src/english_editor/modules/orchestration/domain/value_objects.py
"""
Value Objects para el Bounded Context de Orquestación.

Arquitectura: Modular Monolith
Capa: Domain
Responsabilidad: Definir inmutables para integridad de archivos y estados de procesos.
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto

# === Guía de Organización ===
# ✅ PUREZA: Solo tipos nativos y lógica de validación pura.
# ❌ SIN I/O: No leer disco aquí. Los valores (hash, size) se pasan al constructor.

@dataclass(frozen=True)
class SourceFingerprint:
    """
    Representa la 'huella digital' única de un archivo fuente.
    Implementa la regla de negocio: 'Integridad de Fuente (DR-05)'.

    No confiamos solo en el nombre del archivo. Si el hash o el tamaño cambian,
    es un archivo diferente, invalidando checkpoints previos.
    """
    filename: str
    file_size_bytes: int
    content_hash: str  # Hash parcial o completo (ej: SHA256 de los primeros 10MB)

    def __post_init__(self):
        if not self.filename:
            raise ValueError("El nombre de archivo no puede estar vacío.")
        if self.file_size_bytes < 0:
            raise ValueError("El tamaño del archivo no puede ser negativo.")
        if not self.content_hash:
            raise ValueError("El hash de contenido es obligatorio para garantizar integridad.")

    def matches(self, other: SourceFingerprint) -> bool:
        """
        Verifica si dos huellas corresponden al mismo activo físico,
        ignorando cambios de nombre si el contenido es idéntico,
        o detectando colisiones de nombre con contenido distinto.
        """
        if not isinstance(other, SourceFingerprint):
            return False

        # Regla estricta: El contenido (hash + size) manda sobre el nombre.
        return (
            self.file_size_bytes == other.file_size_bytes and
            self.content_hash == other.content_hash
        )

class JobStatus(Enum):
    """
    Estados posibles del ciclo de vida de procesamiento.
    """
    PENDING = auto()    # En cola, aún no tocado
    IN_PROGRESS = auto() # Checkpoint activo existente
    COMPLETED = auto()   # Finalizado exitosamente (Idempotencia: no reprocesar)
    FAILED = auto()      # Falló, requiere intervención o reintento forzado
    SKIPPED = auto()     # Omitido por idempotencia (ya existía output)

    def is_terminal(self) -> bool:
        """Indica si el estado es final y no requiere más procesamiento activo."""
        return self in (JobStatus.COMPLETED, JobStatus.SKIPPED)

    def can_resume(self) -> bool:
        """Indica si es válido intentar reanudar desde un checkpoint."""
        return self in (JobStatus.IN_PROGRESS, JobStatus.FAILED)