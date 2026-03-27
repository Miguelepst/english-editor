
# @title 📄 use_cases.py — [Application / Use Cases] Orquestador de Renderizado
# ✅ Archivo creado: /content/english-editor/src/english_editor/modules/renderer/application/use_cases.py

# src/english_editor/modules/renderer/application/use_cases.py
"""
Casos de Uso del Renderer.

Arquitectura: Modular Monolith + Vertical Slice
Componente: Application / Use Cases
Responsabilidad: Orquestar la transformación de datos crudos a objetos de dominio, aplicar reglas de negocio y delegar la ejecución I/O al puerto de infraestructura.
"""

from __future__ import annotations

from pathlib import Path

from english_editor.modules.renderer.domain.ports.media_splicer import MediaSplicerPort

# === Imports del proyecto ===
from english_editor.modules.renderer.domain.value_objects import MediaSegment, Padding

# === Definición principal ===


class RenderMediaUseCase:
    """
    Orquestador principal para el corte y renderizado de medios.
    No contiene lógica matemática directa ni llamadas a subprocesos; delega todo al Dominio y a la Infraestructura.
    """

    def __init__(self, splicer: MediaSplicerPort) -> None:
        """
        Inyección de dependencias estricta: requiere una implementación del puerto de dominio.
        """
        self._splicer = splicer

    def execute(
        self,
        source_path: Path,
        raw_segments: list[dict[str, float]],
        padding_ms: float,
        output_path: Path,
        media_duration_ms: float | None = None,  # ✅ NUEVO: Límite superior opcional
    ) -> Path:
        """
        Ejecuta el flujo de renderizado.

        Args:
            source_path: Ruta del archivo original.
            raw_segments: Lista de diccionarios con 'start_ms' y 'end_ms' crudos.
            padding_ms: Milisegundos de padding a aplicar a cada corte.
            output_path: Destino deseado para el archivo final.

        Returns:
            Path: Ruta del archivo generado por el adaptador de infraestructura.
        """
        # 1. Instanciar Value Objects (La validación de dominio ocurre aquí automáticamente)
        pad = Padding(duration_ms=padding_ms)

        # 2. Convertir datos crudos a Entidades Puras y aplicar reglas de negocio
        processed_segments: list[MediaSegment] = []
        for raw in raw_segments:
            # Si start_ms >= end_ms, esto lanzará ValueError antes de tocar la infraestructura
            segment = MediaSegment(start_ms=raw["start_ms"], end_ms=raw["end_ms"])

            # Aplicar matemática de padding (con protección inferior 0.0 y superior max_duration)
            padded_segment = segment.apply_padding(
                pad, max_duration_ms=media_duration_ms
            )
            processed_segments.append(padded_segment)

        # 3. Delegar el trabajo pesado a la infraestructura a través del Puerto
        return self._splicer.splice_and_render(
            source_path=source_path,
            segments=processed_segments,
            output_path=output_path,
        )


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    pass




