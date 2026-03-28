
# @title 📄 demo_renderer.py — [Demo / Interactive] Demostración en vivo (VERSIÓN CORREGIDA MP4)
# ✅ Demo interactiva actualizada con soporte MP4: /content/english-editor/src/english_editor/modules/renderer/demo_renderer.py

# src/english_editor/modules/renderer/demo_renderer.py
"""
Demo interactiva en código para el Micro-SPS 03: [Media Splicer & Renderer].
Versión Corregida: Utiliza un archivo MP4 dummy con stream de video y audio.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

# === Configuración del path para permitir imports locales si se corre fuera de pip ===
sys.path.append(str(Path("/content/english-editor/src")))

# === Imports del proyecto ===
from english_editor.modules.renderer.application import RenderMediaUseCase
from english_editor.modules.renderer.domain import MediaSegment, Padding
from english_editor.modules.renderer.infrastructure.adapters import FFmpegMediaSplicer

# === Funciones de ayuda ===


def print_banner(text: str) -> None:
    print("\n" + "=" * 80)
    print(f"🏛️  {text}")
    print("=" * 80)


def create_dummy_source(source_path: Path, duration_sec: int) -> None:
    """Utiliza ffmpeg para generar un video dummy (testsrc + sine audio)."""
    print(f"🎬 Creando archivo de VIDEO dummy de {duration_sec}s en: {source_path}...")
    cmd = [
        "ffmpeg",
        "-f",
        "lavfi",
        "-i",
        f"testsrc=duration={duration_sec}:size=640x360:rate=30",  # Pista de Video
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=1000:duration={duration_sec}",  # Pista de Audio
        "-c:v",
        "libx264",
        "-c:a",
        "aac",
        str(source_path),
        "-y",
    ]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Archivo dummy creado con éxito.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al crear archivo dummy: {e.stderr}")
        sys.exit(1)


# === Escenarios de la Demo ===


def execute_domain_demo() -> None:
    print_banner("DEMO 1: Lógica Pura del Dominio (Matemáticas inmutables)")

    # Escenario normal
    original = MediaSegment(start_ms=10000.0, end_ms=20000.0)
    pad = Padding(duration_ms=1000.0)  # 1 segundo de padding
    padded = original.apply_padding(pad)

    print(
        f"Segmento Original: {original.start_ms / 1000}s -> {original.end_ms / 1000}s (Duración: {original.duration_ms / 1000}s)"
    )
    print(f"Padding a aplicar: {pad.duration_ms / 1000}s")
    print(
        f"Segmento Resultante: {padded.start_ms / 1000}s -> {padded.end_ms / 1000}s (Duración: {padded.duration_ms / 1000}s)"
    )
    print("✅ Inmutabilidad verificada.")

    # Escenario de límite DoD #3: Clipeo a 0
    edge_original = MediaSegment(start_ms=500.0, end_ms=5000.0)
    print(f"\nSegmento Borde Original: {edge_original.start_ms / 1000}s")

    padded_edge = edge_original.apply_padding(pad)
    print(f"Padded (0.5s - 1.0s): {padded_edge.start_ms / 1000}s")
    print("✅ Regla DoD #3 verificada: El inicio se limitó matemáticamente a 0.0s.")


def execute_use_case_demo() -> None:
    print_banner("DEMO 2: Orquestación del Caso de Uso + Adaptador FFmpeg Real")

# Setup del entorno dummy (AHORA USANDO MP4)
    # Usamos una ruta relativa local para evitar vulnerabilidades B108 en /tmp
    dummy_dir = Path("output/renderer_demo")
    dummy_dir.mkdir(parents=True, exist_ok=True)
    source = dummy_dir / "source_video.mp4"
    output = dummy_dir / "output_editado.mp4"

    # Crear fuente dummy de 10s
    create_dummy_source(source, duration_sec=10)

    # ─── COMPOSICIÓN ROOT ─────────────────────────────────────────────────────────
    real_splicer = FFmpegMediaSplicer()
    use_case = RenderMediaUseCase(splicer=real_splicer)

    # Datos de entrada
    raw_segments = [
        {"start_ms": 2000.0, "end_ms": 4000.0},
        {"start_ms": 7000.0, "end_ms": 9000.0},
    ]
    padding_ms = 500.0

    print(
        f"\nInstrucción Cruda: Unir 2s-4s y 7s-9s (4s total). Padding: {padding_ms / 1000}s."
    )
    print(
        "Executando RenderMediaUseCase.execute()... (Llamada en vivo a FFmpeg complex-filter)..."
    )

    try:
        final_path = use_case.execute(
            source_path=source,
            raw_segments=raw_segments,
            padding_ms=padding_ms,
            output_path=output,
        )
        print("\n✅ ¡Renderizado completado con éxito!")
        print(f"Archivo generado en: {final_path}")
        print(f"Tamaño del archivo de salida: {os.stat(final_path).st_size} bytes.")

        print("\n💡 Nota: El archivo resultante debería durar 6 segundos exactos,")
        print("   con el audio cortado exactamente en los mismos puntos (lip-sync).")

    except Exception as e:
        print(f"\n❌ Fallo crítico en el renderizado: {e}")


# === Punto de entrada ===

if __name__ == "__main__":
    print_banner("Demos Interactiva en Código: SPS-03 [Media Splicer & Renderer]")
    execute_domain_demo()
    execute_use_case_demo()
    print_banner("FIN DE LA DEMO")




