# src/english_editor/modules/renderer/infrastructure/adapters.py
"""
Adaptadores de Infraestructura del Renderer.

Arquitectura: Modular Monolith + Vertical Slice
Componente: Infrastructure / Adapters
Responsabilidad: Implementar los puertos del dominio interactuando con I/O real (subprocess, disco, binarios externos como FFmpeg).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

# === Imports del proyecto ===
from english_editor.modules.renderer.domain.ports.media_splicer import (
    MediaSplicerPort,
    RenderExecutionError,
)
from english_editor.modules.renderer.domain.value_objects import MediaSegment

# === Definición principal ===


class FFmpegMediaSplicer(MediaSplicerPort):
    """
    Implementación concreta del MediaSplicerPort utilizando el binario del sistema FFmpeg.
    """

    def splice_and_render(
        self, source_path: Path, segments: list[MediaSegment], output_path: Path
    ) -> Path:
        """
        Construye y ejecuta un comando FFmpeg complex-filter para cortar y empalmar medios.
        """
        if not source_path.exists():
            raise FileNotFoundError(
                f"El archivo fuente no existe en la ruta: {source_path}"
            )

        if not segments:
            # Si no hay segmentos, simplemente copiamos el archivo original (o devolvemos el mismo)
            return source_path

        # Construir el grafo de filtros (filter_complex)
        filter_parts: list[str] = []
        concat_inputs = ""

        for i, seg in enumerate(segments):
            # FFmpeg usa segundos en formato float
            start_sec = seg.start_ms / 1000.0
            end_sec = seg.end_ms / 1000.0

            # Extraer y resetear timestamps de VIDEO
            filter_parts.append(
                f"[0:v]trim=start={start_sec}:end={end_sec},setpts=PTS-STARTPTS[v{i}];"
            )
            # Extraer y resetear timestamps de AUDIO
            filter_parts.append(
                f"[0:a]atrim=start={start_sec}:end={end_sec},asetpts=PTS-STARTPTS[a{i}];"
            )

            # Acumular referencias para el nodo de concatenación
            concat_inputs += f"[v{i}][a{i}]"

        # Añadir el nodo final de concatenación
        filter_parts.append(
            f"{concat_inputs}concat=n={len(segments)}:v=1:a=1[outv][outa]"
        )
        filter_complex = "".join(filter_parts)

        # Construir el comando final
        cmd = [
            "ffmpeg",
            "-y",  # Sobrescribir si existe
            "-i",
            str(source_path),  # Archivo de entrada
            "-filter_complex",
            filter_complex,
            "-map",
            "[outv]",  # Mapear salida de video
            "-map",
            "[outa]",  # Mapear salida de audio
            str(output_path),  # Archivo de salida
        ]

        try:
            # Ejecutar de forma segura, capturando stderr para debugging en caso de error
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            return output_path
        except subprocess.CalledProcessError as e:
            # Traducir la excepción de la librería/OS a una excepción pura de nuestro Dominio
            error_details = e.stderr if e.stderr else str(e)
            raise RenderExecutionError(
                f"Fallo en la ejecución de FFmpeg: {error_details}"
            ) from e


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    pass
