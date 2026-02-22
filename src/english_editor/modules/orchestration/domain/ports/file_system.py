# src/english_editor/modules/orchestration/domain/ports/file_system.py
"""
Puerto (Interface) para operaciones de sistema de archivos requeridas por el dominio.

Arquitectura: Modular Monolith
Capa: Domain -> Ports
Responsabilidad: Abstraer verificación de existencia y cálculo de integridad.
"""

from abc import ABC, abstractmethod

from english_editor.modules.orchestration.domain.value_objects import SourceFingerprint


class FileSystemPort(ABC):
    """
    Contrato para interactuar con el almacenamiento de archivos (Local o Cloud).
    """

    @abstractmethod
    def exists(self, path: str) -> bool:
        """
        Verifica si un archivo existe.
        Uso: Regla de Idempotencia (verificar si output ya está creado).
        """
        pass

    @abstractmethod
    def calculate_fingerprint(self, path: str) -> SourceFingerprint:
        """
        Calcula la huella digital (Hash + Size) de un archivo físico.
        La lógica de CÓMO se lee el archivo (chunks, todo en memoria) pertenece a Infraestructura.
        """
        pass

    @abstractmethod
    def list_files(self, directory: str, extensions: list[str]) -> list[str]:
        """
        Lista archivos en un directorio que coincidan con las extensiones.
        Uso: Batch processing.
        """
        pass
