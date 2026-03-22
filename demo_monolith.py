"""
Demostración de la Raíz de Composición (Composition Root).
Une SPS-01, SPS-02 (Fakes) y SPS-03 (Real) en un solo flujo.
"""
from pathlib import Path
from dataclasses import dataclass

# === 1. IMPORTS DE TUS CONTRATOS (PUERTOS) ===
# Asumimos que estas clases ya existen según tu especificación
from english_editor.modules.orchestration.domain.ports.file_system import FileSystemPort
from english_editor.modules.orchestration.domain.ports.repository import JobRepository
from english_editor.modules.analysis.domain.ports.engine import SpeechAnalysisEngine
from english_editor.modules.renderer.domain.ports.media_splicer import MediaSplicerPort

# === 2. IMPORTS DE APLICACIÓN E INFRAESTRUCTURA ===
from english_editor.modules.orchestration.application.use_cases import ProcessVideoWorkflow
from english_editor.modules.renderer.application.use_cases import RenderMediaUseCase
from english_editor.modules.renderer.infrastructure.adapters import FFmpegMediaSplicer


# === 3. ADAPTADORES "FAKE" PARA LA PRUEBA (SPS-01 y SPS-02) ===

# Simulamos el objeto TimeRange que devuelve tu SPS-02
@dataclass
class DummyTimeRange:
    start_ms: float
    end_ms: float

class FakeFileSystem(FileSystemPort):
    def exists(self, path: str) -> bool:
        return True
    def calculate_fingerprint(self, path: str):
        return "fake-hash-12345" # Simula el SourceFingerprint
    def list_files(self, directory: str, extensions: list[str]) -> list[str]:
        return []

class FakeJobRepository(JobRepository):
    def save(self, job) -> None:
        print(f"💾 [Repo] Guardando estado del trabajo...")
    def find_last_by_fingerprint(self, fingerprint):
        return None

class FakeSpeechEngine(SpeechAnalysisEngine):
    def detect_voice_activity(self, audio_path: Path) -> list:
        print(f"🎙️ [Whisper Fake] Analizando audio de {audio_path.name}...")
        # Simulamos que Whisper encontró habla humana en estos dos segmentos
        return [
            DummyTimeRange(start_ms=2000.0, end_ms=4000.0),
            DummyTimeRange(start_ms=7000.0, end_ms=9000.0)
        ]


# === 4. RAÍZ DE COMPOSICIÓN Y EJECUCIÓN ===

def main():
    print("="*80)
    print("⚙️ INICIANDO EL MONOLITO MODULAR (PRUEBA DE INTEGRACIÓN)")
    print("="*80)

    # Rutas de prueba (usaremos el video dummy que creamos antes)
    input_video = Path("/tmp/renderer_demo/source_video.mp4")
    output_video = Path("/tmp/renderer_demo/final_monolith_output.mp4")

    if not input_video.exists():
        print("❌ El video de prueba no existe. Ejecuta primero la demo del renderer.")
        return

    # --- A. INSTANCIAR ADAPTADORES ---
    fs_adapter = FakeFileSystem()
    repo_adapter = FakeJobRepository()
    speech_adapter = FakeSpeechEngine()
    ffmpeg_adapter = FFmpegMediaSplicer() # ¡ESTE ES REAL!

    # --- B. ENSAMBLAR CASOS DE USO (Inyección de Dependencias) ---
    # El renderer recibe a FFmpeg
    renderer_use_case = RenderMediaUseCase(splicer=ffmpeg_adapter)
    
    # El orquestador recibe TODO
    orchestrator = ProcessVideoWorkflow(
        file_system=fs_adapter,
        repository=repo_adapter,
        analysis_engine=speech_adapter,
        renderer=renderer_use_case
    )

    # --- C. EJECUTAR EL FLUJO MAESTRO ---
    try:
        resultado = orchestrator.execute(
            input_path=input_video,
            output_path=output_video,
            padding_ms=500.0 # Medio segundo de margen
        )
        print("\n🎉 ¡FLUJO COMPLETO TERMINADO EXITOSAMENTE!")
        print(f"🎬 Archivo final disponible en: {resultado}")
    except Exception as e:
        print(f"\n❌ Error en la orquestación: {e}")

if __name__ == "__main__":
    main()
