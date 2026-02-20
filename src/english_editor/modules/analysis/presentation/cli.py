# src/english_editor/modules/analysis/presentation/cli.py
"""
Interfaz de Línea de Comandos (CLI) para Análisis de Voz.

Arquitectura: Presentation Layer (Interface Adapter)
Responsabilidad:
    1. Parsear argumentos (argv).
    2. Instanciar el Composition Root.
    3. Formatear la salida (JSON/Texto).
"""

import argparse
import sys
import json
import time
from pathlib import Path

# Imports del núcleo (asumiendo ejecución como módulo o con PYTHONPATH correcto)
# Si se ejecuta directamente, el path debe estar configurado externamente o aquí.
try:
    from english_editor.modules.analysis.infrastructure.whisper_adapter import (
        WhisperLocalAdapter,
    )
    from english_editor.modules.analysis.application.use_cases import AnalyzeAudio
    from english_editor.modules.analysis.domain.exceptions import AnalysisError
except ImportError:
    # Hack para desarrollo local si no está instalado como paquete
    sys.path.append(str(Path(__file__).resolve().parents[4]))
    from english_editor.modules.analysis.infrastructure.whisper_adapter import (
        WhisperLocalAdapter,
    )
    from english_editor.modules.analysis.application.use_cases import AnalyzeAudio
    from english_editor.modules.analysis.domain.exceptions import AnalysisError


def setup_parser() -> argparse.ArgumentParser:
    """Configura los argumentos aceptados por la herramienta."""
    parser = argparse.ArgumentParser(
        description="🇬🇧 English Editor - Speech Analysis Tool",
        epilog="Ejemplo: python -m english_editor.modules.analysis.presentation.cli input.wav --json",
    )

    parser.add_argument(
        "input_file", type=Path, help="Ruta al archivo de audio (.wav, .mp3, etc.)"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="tiny.en",
        choices=["tiny.en", "base.en", "small.en"],
        help="Tamaño del modelo Whisper (default: tiny.en)",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en formato JSON (útil para tuberías/pipes)",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Muestra logs detallados de progreso",
    )

    return parser


def format_output_text(segments, duration_sec: float):
    """Presentación amigable para humanos."""
    print(f"\n📊 ANÁLISIS COMPLETADO ({duration_sec:.2f}s)")
    print("=" * 60)
    print(f"{'ID':<4} | {'INICIO':<10} | {'FIN':<10} | {'DURACIÓN':<10}")
    print("-" * 60)

    if not segments:
        print("   (Sin actividad de voz detectada)")
    else:
        for i, seg in enumerate(segments, 1):
            print(
                f"{i:<4} | {seg.start:>8.2f}s | {seg.end:>8.2f}s | {seg.duration:>8.2f}s"
            )

    print("=" * 60)
    print(f"Total segmentos: {len(segments)}")


def format_output_json(segments):
    """Presentación para máquinas (Machine Readable)."""
    data = [
        {"start": seg.start, "end": seg.end, "duration": seg.duration}
        for seg in segments
    ]
    print(json.dumps(data, indent=2))


def main():
    parser = setup_parser()
    args = parser.parse_args()

    # 1. Validación de Presentación
    if not args.input_file.exists():
        print(f"❌ Error: El archivo '{args.input_file}' no existe.", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"⚙️  Cargando modelo {args.model} en CPU...")

    try:
        # 2. Composition Root (Wiring)
        # Aquí conectamos las capas: Infraestructura -> Aplicación
        adapter = WhisperLocalAdapter(model_size=args.model)
        use_case = AnalyzeAudio(engine=adapter)

        # 3. Ejecución
        if args.verbose:
            print("🚀 Procesando audio...")

        start_time = time.time()
        segments = use_case.execute(args.input_file)
        elapsed = time.time() - start_time

        # 4. Renderizado (Output)
        if args.json:
            format_output_json(segments)
        else:
            format_output_text(segments, elapsed)

    except AnalysisError as e:
        # Capturamos errores de Dominio y los mostramos bonitos
        print(f"❌ Error de Análisis: {e}", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n⚠️  Operación cancelada por el usuario.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        # Errores inesperados (Bugs)
        print(f"❌ Error Crítico: {e}", file=sys.stderr)
        sys.exit(3)


if __name__ == "__main__":
    main()
