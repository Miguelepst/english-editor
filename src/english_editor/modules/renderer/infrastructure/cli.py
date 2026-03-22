# src/english_editor/modules/renderer/infrastructure/cli.py
"""
Interfaz de Línea de Comandos (CLI) para el Renderer.

Arquitectura: Modular Monolith + Vertical Slice
Componente: Infrastructure / Adapters (Primary/Driving Adapter)
Responsabilidad: Parsear argumentos del usuario, traducir la UX (segundos) al lenguaje del dominio (milisegundos) y orquestar la ejecución mostrando errores limpios.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

# === Imports del proyecto ===
from english_editor.modules.renderer.application.use_cases import RenderMediaUseCase
from english_editor.modules.renderer.infrastructure.adapters import FFmpegMediaSplicer

def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Configura y parsea los argumentos de la terminal."""
    parser = argparse.ArgumentParser(
        description="Media Splicer & Renderer - Corta y empalma video/audio con precisión."
    )
    
    parser.add_argument(
        "-s", "--source", 
        type=str, 
        required=True, 
        help="Ruta al archivo multimedia de origen."
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        required=True, 
        help="Ruta de destino para el archivo editado."
    )
    parser.add_argument(
        "-t", "--segments", 
        nargs="+", 
        required=True,
        help="Lista de segmentos a mantener en formato 'inicio,fin' (EN SEGUNDOS). Ej: -t 2.0,5.5 10.0,15.0"
    )
    parser.add_argument(
        "-p", "--padding", 
        type=float, 
        default=0.0,
        help="Margen de seguridad a inyectar a cada corte (EN MILISEGUNDOS). Ej: 500 para medio segundo."
    )
    
    return parser.parse_args(args)

def main() -> None:
    """Punto de entrada principal para la ejecución desde terminal."""
    # Parsear los argumentos (omitiendo el nombre del script en sys.argv[0])
    args = parse_args(sys.argv[1:])
    
    # 1. Traducción Frontera -> Dominio (UX: Segundos -> Core: Milisegundos)
    raw_segments: list[dict[str, float]] = []
    try:
        for seg_str in args.segments:
            start_str, end_str = seg_str.split(",")
            start_sec = float(start_str.strip())
            end_sec = float(end_str.strip())
            
            raw_segments.append({
                "start_ms": start_sec * 1000.0,
                "end_ms": end_sec * 1000.0
            })
    except ValueError:
        print("❌ Error de formato: Los segmentos deben tener el formato 'inicio,fin' con números. Ej: 2.5,5.0", file=sys.stderr)
        sys.exit(1)

    source_path = Path(args.source)
    output_path = Path(args.output)
    padding_ms = args.padding

    # 2. Composition Root & Ejecución
    print(f"🎬 Iniciando renderizado de {source_path.name}...")
    print(f"   Segmentos a procesar: {len(raw_segments)} | Padding de seguridad: {padding_ms}ms")
    
    try:
        # Instanciamos la infraestructura y la inyectamos al caso de uso
        splicer = FFmpegMediaSplicer()
        use_case = RenderMediaUseCase(splicer=splicer)
        
        # Ejecutamos la orquestación
        result_path = use_case.execute(
            source_path=source_path,
            raw_segments=raw_segments,
            padding_ms=padding_ms,
            output_path=output_path
        )
        
        print(f"✅ ¡Éxito! Archivo renderizado guardado en: {result_path}")
        
    except Exception as e:
        # 3. Manejo limpio de errores (ocultando el stacktrace al usuario)
        print(f"\n❌ Error durante el proceso:\n   {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
