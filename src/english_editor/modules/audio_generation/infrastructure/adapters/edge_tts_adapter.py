# src/english_editor/modules/audio_generation/infrastructure/adapters/edge_tts_adapter.py
"""
Adaptador síncrono para edge-tts simulando la interfaz de gTTS.

Arquitectura: Modular Monolith + Vertical Slice
Componente: Infrastructure Adapter
Responsabilidad: Encapsular la complejidad asíncrona de edge-tts y exponer
una API síncrona idéntica a gTTS para evitar refactorizaciones masivas.
"""

from __future__ import annotations

# === Imports estándar ===
import asyncio
from typing import Any

# === Imports del proyecto ===
import edge_tts

# 👇 EL TRUCO INVISIBLE: Se ejecuta automáticamente al importar la clase
import nest_asyncio

nest_asyncio.apply()
# 👆 FIN DEL TRUCO


# === Definición principal ===
class gTTS_edge:
    """
    Máscara de compatibilidad (Adapter Pattern) para edge-tts.
    """

    # def __init__(self, text: str, lang: str = "en", **kwargs: dict) -> None:
    def __init__(
        self, text: str, lang: str = "en", **kwargs: Any
    ) -> None:  # mypy linter
        self.text = text
        voces_por_defecto = {"en": "en-US-AriaNeural", "es": "es-ES-AlvaroNeural"}
        self.voice = voces_por_defecto.get(lang, "en-US-AriaNeural")

    def save(self, savefile: str) -> None:
        """Soporte para guardado tradicional en disco."""
        communicate = edge_tts.Communicate(text=self.text, voice=self.voice)
        asyncio.run(communicate.save(savefile))

    def write_to_fp(self, fp) -> None:
        """
        ¡Nuevo! Soporte para escribir en memoria (BytesIO) igual que gTTS.
        Extrae los fragmentos binarios de audio al vuelo y los inyecta en el buffer.
        """

        async def _stream_to_fp():
            communicate = edge_tts.Communicate(text=self.text, voice=self.voice)
            # stream() nos permite capturar los bytes en tiempo real sin tocar el disco
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    fp.write(chunk["data"])

        # Bloqueamos el hilo temporalmente para cumplir el contrato síncrono
        asyncio.run(_stream_to_fp())


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    pass
