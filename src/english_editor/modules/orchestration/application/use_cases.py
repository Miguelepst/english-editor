
# @title 📄 use_cases.py — [Application] Instrumentado 📊

# ✅ Archivo creado (Casos de Uso Creado e Instrumentados): /content/english-editor/src/english_editor/modules/orchestration/application/use_cases.py
# 📦 Repo GitHub:    'english-editor'  (kebab-case → github.com/.../english-editor)
# 📦 Paquete Python: 'english_editor'  (snake_case → imports: from english_editor.modules...)
# 💡 Lógica Clave: 'prepare_jobs' es un generador (yield). Esto permite procesar miles de archivos sin cargar todos los objetos Job en memoria a la vez.

# src/english_editor/modules/orchestration/application/use_cases.py
from pathlib import Path

# Imports de Puertos de Orquestación (SPS-01)
from english_editor.modules.orchestration.domain.ports.file_system import FileSystemPort
from english_editor.modules.orchestration.domain.ports.repository import JobRepository
from english_editor.modules.orchestration.domain.entities import ProcessingJob

# Imports de Contratos de Análisis (SPS-02)
from english_editor.modules.analysis.domain.ports.engine import SpeechAnalysisEngine

# Imports de Contratos de Renderizado (SPS-03)
from english_editor.modules.renderer.application.use_cases import RenderMediaUseCase

class ProcessVideoWorkflow:
    """
    El Director de Orquesta.
    Coordina la lectura (SPS-01), el análisis (SPS-02) y el renderizado (SPS-03).
    """

    def __init__(self, repository: JobRepository, file_system: FileSystemPort):
        # Inyección de Dependencias (DIP)
        self.repo = repository
        self.fs = file_system

    def prepare_jobs(
        self, input_path: str, output_dir: str, force: bool = False
    ) -> Iterator[ProcessingJob]:
        """
        Analiza la entrada y genera un flujo de trabajos.
        """
        logger.info(f"Iniciando preparación de jobs. Input: {input_path}")
        """
        Analiza la entrada y genera un flujo de trabajos listos para procesar.
        """
        # 1. Resolver lista de archivos (Batch vs Single)
        files_to_process = self._resolve_input_files(input_path)
        logger.info(f"Total archivos candidatos: {len(files_to_process)}")

        stats = {"processed": 0, "skipped": 0, "resumed": 0, "new": 0}

        for source_path in files_to_process:
            # 2. Definir ruta de salida esperada
            filename = os.path.basename(source_path)
            name_only, ext = os.path.splitext(filename)
            expected_output = os.path.join(output_dir, f"{name_only}_editado{ext}")

            # 3. Regla de Idempotencia: Si existe y no forzamos, saltar.
            if self.fs.exists(expected_output) and not force:
                logger.info(f"[SKIP] Output ya existe para: {filename}")
                stats["skipped"] += 1
                # Podríamos loggear aquí: "Skipping {filename}, output exists."
                continue

            # 4. Regla de Integridad: Calcular Fingerprint
            # Esto garantiza que detectamos cambios de contenido (DR-05)
            fingerprint = self.fs.calculate_fingerprint(source_path)

            # 5. Regla de Recuperación: Buscar trabajo previo
            existing_job = self.repo.find_last_by_fingerprint(fingerprint)

            if existing_job and existing_job.status.can_resume() and not force:
                logger.info(
                    f"[RESUME] Job encontrado para: {filename} (ID: {existing_job.job_id})"
                )
                stats["resumed"] += 1
                # REANUDAR: Devolvemos el trabajo con su progreso guardado
                yield existing_job
            else:
                if existing_job:
                    logger.info(
                        f"[RESTART] Job previo terminado o inválido, iniciando nuevo para: {filename}"
                    )

                # NUEVO: Creamos un trabajo limpio
                new_job = ProcessingJob.create_new(fingerprint, expected_output)
                self.repo.save(new_job)  # Persistir estado inicial inmediatamente
                logger.info(f"[NEW] Job creado: {new_job.job_id} para {filename}")
                stats["new"] += 1
                yield new_job

            stats["processed"] += 1

        logger.info(f"Resumen de Batch: {stats}")

    def _resolve_input_files(self, path: str) -> list[str]:
        """Helper para aplanar directorios o validar archivos individuales."""
        # Nota: La lógica de "es directorio" vs "es archivo" podría delegarse al FileSystemPort
        # para pureza total, pero os.path.isdir es aceptable en Application si asumimos POSIX.
        # Para ser estrictos con la arquitectura, usaremos el FileSystemPort si tuviera is_dir,
        # pero asumiremos que input_path viene validado o delegamos a una lógica simple.

        # Simplificación: Asumimos que FileSystemPort.list_files maneja la lógica de descubrimiento
        # Si es un archivo directo, lo devolvemos en lista.
        if path.endswith(
            (".mp4", ".mp3", ".wav")
        ):  # Extensiones harcodeadas por brevedad, ideal config
            return [path]

        # Si es directorio (asumimos por falta de extensión o lógica de negocio), pedimos listar.
        return self.fs.list_files(path, extensions=[".mp4", ".mp3", ".wav"])









