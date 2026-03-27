
# @title 📄 Interfaz media_splicer.py — [Domain / Ports] Contrato para el motor de renderizado

# ✅ Archivo creado: /content/english-editor/src/english_editor/modules/renderer/domain/ports/media_splicer.py
# 📦 Repo GitHub:    'english-editor'
# 💡 Import válido: from english_editor.modules.renderer.domain.ports.media_splicer import MediaSplicerPort

# src/english_editor/modules/renderer/domain/ports/media_splicer.py
"""
Puerto de Dominio para el Media Splicer (Contrato de Infraestructura).

Arquitectura: Modular Monolith + Vertical Slice
Componente: Domain / Ports
Responsabilidad: Definir la interfaz estricta que cualquier motor de renderizado (ej: FFmpeg) debe implementar para ser compatible con nuestro sistema.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

# === Imports del proyecto ===
from english_editor.modules.renderer.domain.value_objects import MediaSegment


# === Excepciones de Dominio ===
class RenderExecutionError(Exception):
    """Excepción lanzada cuando el motor subyacente falla al procesar los medios."""

    pass


# === Definición principal ===


class MediaSplicerPort(Protocol):
    """
    Contrato de dominio para el motor de renderizado y empalme.
    Garantiza que la aplicación no dependa de implementaciones concretas como FFmpeg.
    """

    def splice_and_render(
        self, source_path: Path, segments: list[MediaSegment], output_path: Path
    ) -> Path:
        """
        Extrae y concatena los segmentos especificados del archivo fuente con precisión.

        Args:
            source_path: Ruta absoluta al archivo multimedia original (solo lectura).
            segments: Lista cronológica de intervalos inmutables a mantener.
            output_path: Ruta de destino esperada para el archivo editado.

        Returns:
            Path: La ruta absoluta del archivo resultante generado (suele coincidir con output_path).

        Raises:
            RenderExecutionError: Si ocurre un fallo en el proceso externo o corrupción de codec.
            FileNotFoundError: Si el archivo fuente no existe.
        """
        ...


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    pass



