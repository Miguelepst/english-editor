# src/english_editor/cli.py
"""
CLI Global y Raíz de Composición.
Este es el ÚNICO lugar donde los módulos conocen sus detalles de infraestructura.
"""
import argparse
import sys
from pathlib import Path

# --- 1. Imports de Infraestructura (Adaptadores Concretos) ---
# Sustituye estos nombres por los nombres reales de las clases que construiste
from english_editor.modules.orchestration.infrastructure.adapters import LocalFileSystemAdapter, JsonJobRepository
from english_editor.modules.analysis.infrastructure.adapters import WhisperLocalAdapter
from english_editor.modules.renderer.infrastructure.adapters import FFmpegMediaSplicer

# --- 2. Imports de Aplicación (Casos de Uso) ---
from english_editor.modules.renderer.application.use_cases import RenderMediaUseCase
from english_editor.modules.orchestration.application.use_cases import ProcessVideoWorkflow


def main():
    parser = argparse.ArgumentParser(description="English Editor - Procesador Mágico de Video")
    parser.add_argument("-s", "--source", required=True, help="Video de entrada")
    parser.add_argument("-o", "--output", required=True, help="Video de salida")
    parser.add_argument("-p", "--padding", type=float, default=500.0, help="Padding en ms")
    args = parser.parse_args()

    input_path = Path(args.source)
    output_path = Path(args.output)

    try:
        # === RAÍZ DE COMPOSICIÓN (El Engranaje) ===
        
        # 1. Instanciar Adaptadores (Hardware/APIs)
        file_system = LocalFileSystemAdapter()
        repository = JsonJobRepository(db_path="/tmp/jobs.json")
        analyzer_engine = WhisperLocalAdapter() # Tu motor de SPS-02
        splicer_engine = FFmpegMediaSplicer()   # El motor de SPS-03
        
        # 2. Ensamblar Casos de Uso (Inyección de Dependencias)
        renderer_uc = RenderMediaUseCase(splicer=splicer_engine)
        
        # 3. Ensamblar el Orquestador Maestro (Inyectamos todo)
        orchestrator = ProcessVideoWorkflow(
            file_system=file_system,
            repository=repository,
            analysis_engine=analyzer_engine,
            renderer=renderer_uc
        )

        # === EJECUCIÓN ===
        orchestrator.execute(
            input_path=input_path, 
            output_path=output_path, 
            padding_ms=args.padding
        )

    except Exception as e:
        print(f"\n❌ Error Catastrófico en la Orquestación: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
