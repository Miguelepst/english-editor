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

    def __init__(
        self,
        file_system: FileSystemPort,
        repository: JobRepository,
        analysis_engine: SpeechAnalysisEngine,
        renderer: RenderMediaUseCase
    ):
        self._fs = file_system
        self._repo = repository
        self._analyzer = analysis_engine
        self._renderer = renderer

    def execute(self, input_path: Path, output_path: Path, padding_ms: float = 0.0) -> Path:
        print("🧠 [SPS-01] Iniciando flujo maestro de orquestación...")

        # 1. VERIFICACIÓN Y ESTADO (SPS-01)
        fingerprint = self._fs.calculate_fingerprint(str(input_path))
        
        # ✅ CORRECCIÓN: Usamos el Factory Method de tu entidad
        job = ProcessingJob.create_new(source=fingerprint, output_path=str(output_path))
        self._repo.save(job)

        try:
            # 2. ANÁLISIS DE VOZ (SPS-02)
            print("🕵️‍♂️ [SPS-02] Extrayendo y analizando silencios/voz...")
            time_ranges = self._analyzer.detect_voice_activity(input_path)
            
            if not time_ranges:
                job.fail_job("No se detectó voz en el archivo.")
                self._repo.save(job)
                raise ValueError("No se detectó voz en el archivo. Abortando.")

            # 3. TRADUCCIÓN DE DOMINIOS
            print(f"🔄 [SPS-01] Mapeando {len(time_ranges)} segmentos detectados al motor de renderizado...")
            raw_segments_for_renderer = []
            for tr in time_ranges:
                raw_segments_for_renderer.append({"start_ms": tr.start_ms, "end_ms": tr.end_ms})
                # Actualizamos el estado de la entidad por cada segmento
                job.mark_segment_processed(start_time=tr.start_ms, end_time=tr.end_ms)
            
            self._repo.save(job)

            # 4. RENDERIZADO Y CORTE (SPS-03)
            print("✂️ [SPS-03] Ejecutando corte de video por FFmpeg...")
            final_path = self._renderer.execute(
                source_path=input_path,
                raw_segments=raw_segments_for_renderer,
                padding_ms=padding_ms,
                output_path=output_path
            )

            # 5. FINALIZACIÓN
            print("✅ [SPS-01] Flujo maestro completado con éxito.")
            job.complete_job()
            self._repo.save(job)
            return final_path

        except Exception as e:
            # Si cualquier cosa falla (Whisper o FFmpeg), el orquestador atrapa el error y actualiza el estado
            job.fail_job(reason=str(e))
            self._repo.save(job)
            raise e
