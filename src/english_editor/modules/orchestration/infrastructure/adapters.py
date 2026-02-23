# src/english_editor/modules/orchestration/infrastructure/adapters.py
"""
Adaptadores de Infraestructura para Orquestación.

Arquitectura: Modular Monolith
Capa: Infrastructure (Adapters)
Responsabilidad: Implementar los puertos del dominio usando tecnologías concretas (JSON, OS).
"""

# ✅ IMPORTS ORDENADOS: stdlib 'import' antes que 'from', alfabético por módulo
import glob
import hashlib
import json
import logging
import os
from datetime import datetime
from typing import Any, Optional, cast

from english_editor.modules.orchestration.domain.entities import ProcessingJob
from english_editor.modules.orchestration.domain.ports.file_system import FileSystemPort

# === Imports de Dominio ===
from english_editor.modules.orchestration.domain.ports.repository import JobRepository
from english_editor.modules.orchestration.domain.value_objects import (
    JobStatus,
    SourceFingerprint,
)
from english_editor.modules.orchestration.infrastructure.observability import (
    measure_time,
)

# ... (resto del código igual)


"""
Adaptadores de Infraestructura con Telemetría.
"""
# import logging
# Importamos el decorador de métricas
# from english_editor.modules.orchestration.infrastructure.observability import measure_time

logger = logging.getLogger(__name__)


class LocalFileSystemAdapter(FileSystemPort):
    """
    Implementación que interactúa con el sistema de archivos local del OS.
    """

    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    @measure_time(metric_name="hashing_latency")
    def calculate_fingerprint(self, path: str) -> SourceFingerprint:
        """
        Genera una huella digital única.
        Estrategia 'Smart Hash': Hash de (Tamaño + Inicio 64KB + Final 64KB).
        Mucho más rápido que hashear todo el archivo para videos grandes.
        """
        """
        Calcula fingerprint con métricas de latencia.
        """
        logger.debug(f"Calculando fingerprint para: {path}")

        if not os.path.exists(path):
            logger.error(f"Archivo no encontrado: {path}")
            raise FileNotFoundError(
                f"No se puede calcular fingerprint: {path} no existe"
            )

        file_size = os.path.getsize(path)
        filename = os.path.basename(path)

        hasher = hashlib.sha256()

        # ❌ Antes:
        # 1. Hashear metadatos clave
        # hasher.update(f"{filename}-{file_size}".encode('utf-8'))   # .encode("utf-8") es redundante (UTF-8 es default)

        # ✅ Después:
        hasher.update(f"{filename}-{file_size}".encode())

        # 2. Hashear contenido parcial (Optimización)
        with open(path, "rb") as f:
            # Leer inicio
            chunk_head = f.read(65536)
            hasher.update(chunk_head)

            # Leer final (si el archivo es grande)
            if file_size > 65536 * 2:
                f.seek(-65536, os.SEEK_END)
                chunk_tail = f.read(65536)
                hasher.update(chunk_tail)

        fingerprint = SourceFingerprint(
            filename=filename,
            file_size_bytes=file_size,
            content_hash=hasher.hexdigest(),
        )
        logger.debug(f"Fingerprint generado: {fingerprint.content_hash[:8]}...")
        return fingerprint

        # return SourceFingerprint(
        #    filename=filename,
        #    file_size_bytes=file_size,
        #    content_hash=hasher.hexdigest()
        # )

    # def list_files(self, directory: str, extensions: List[str]) -> List[str]:
    def list_files(self, directory: str, extensions: list[str]) -> list[str]:
        files = []
        if not os.path.isdir(directory):
            logger.warning(f"Directorio de entrada no existe: {directory}")
            return []

        for ext in extensions:
            pattern = os.path.join(directory, f"*{ext}")
            found = glob.glob(pattern)
            files.extend(found)

        logger.info(f"Archivos encontrados en {directory}: {len(files)}")
        return sorted(files)

        # Búsqueda insensible a mayúsculas/minúsculas simple
        # pattern = os.path.join(directory, f"*{ext}")
        # files.extend(glob.glob(pattern))
        # return sorted(files)


class JsonFileRepository(JobRepository):
    """
    Persistencia simple basada en un archivo JSON único.
    Ideal para entornos como Colab donde no hay base de datos dedicada.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        if not os.path.exists(self.db_path):
            logger.info(f"Inicializando nueva DB en: {self.db_path}")
            with open(self.db_path, "w") as f:
                json.dump({"jobs": {}}, f)

    def _load_db(self) -> dict[str, Any]:
        try:
            # ❌ Antes:
            # with open(self.db_path, 'r') as f:
            # ✅ Después:
            with open(
                self.db_path
            ) as f:  # open(path, "r") no necesita "r" (es default)
                # ✅ Casting explícito para mypy: no-any-return
                return cast(dict[str, Any], json.load(f))
        except json.JSONDecodeError:
            logger.error(f"DB corrupta en {self.db_path}, iniciando vacía.")
            return {"jobs": {}}

    """
    #def _load_db(self) -> Dict[str, Any]:
    def _load_db(self) -> dict[str, Any]:
        try:
            #with open(self.db_path, 'r') as f:
            with open(self.db_path) as f:                        # open(path, "r") no necesita "r" (es default)
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"DB corrupta en {self.db_path}, iniciando vacía.")
            return {"jobs": {}}

    """

    # def _save_db(self, data: Dict[str, Any]):
    def _save_db(self, data: dict[str, Any]):
        # Escritura atómica simulada (write + rename es mejor, pero simple aquí)
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def save(self, job: ProcessingJob) -> None:
        data = self._load_db()

        # Mapping: Entity -> DTO (Dict)
        job_dto = {
            "job_id": job.job_id,
            "filename": job.source.filename,
            "file_size": job.source.file_size_bytes,
            "content_hash": job.source.content_hash,
            "output_path": job.output_path,
            "status": job.status.name,
            "checkpoints": job.get_checkpoints_copy(),
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "error_message": job.error_message,
        }

        # Usamos el content_hash como clave de indexación secundaria o el ID
        data["jobs"][job.source.content_hash] = job_dto
        self._save_db(data)
        logger.debug(f"Job guardado: {job.job_id} | Status: {job.status.name}")

    def find_last_by_fingerprint(
        self, fingerprint: SourceFingerprint
    ) -> Optional[ProcessingJob]:
        data = self._load_db()
        job_data = data["jobs"].get(fingerprint.content_hash)

        if not job_data:
            return None

        # Mapping: DTO -> Entity
        # Reconstrucción del objeto
        try:
            source = SourceFingerprint(
                filename=job_data["filename"],
                file_size_bytes=job_data["file_size"],
                content_hash=job_data["content_hash"],
            )

            job = ProcessingJob(
                job_id=job_data["job_id"],
                source=source,
                output_path=job_data["output_path"],
                created_at=datetime.fromisoformat(job_data["created_at"]),
                status=JobStatus[job_data["status"]],
                # Acceso directo a atributo privado permitido en reconstrucción o usar setter
                _checkpoints=job_data["checkpoints"],
                error_message=job_data.get("error_message"),
                updated_at=datetime.fromisoformat(job_data["updated_at"]),
            )
            return job
        except Exception as e:
            logger.error(f"Error reconstruyendo job desde DB: {e}", exc_info=True)

            # except (KeyError, ValueError) as e:
            # Si el JSON está corrupto o el esquema cambió, lo tratamos como inexistente
            # o loggeamos error.
            # print(f"Warning: Error reconstruyendo job: {e}")
            return None
