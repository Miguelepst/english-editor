# src/english_editor/modules/processing/infrastructure/audio/generate_complex_audio.py
"""
Generador de audio de prueba con segmentos y silencios.

Arquitectura: Modular Monolith + Vertical Slice
Componente: infrastructure
Responsabilidad: Generar archivos de audio de prueba utilizando TTS
y silencios intermedios para validar segmentación de audio.
"""

from __future__ import annotations

import os
import warnings
from io import BytesIO

from pydub import AudioSegment

from english_editor.modules.audio_generation.infrastructure.adapters.edge_tts_adapter import (
    gTTS_edge as gTTS,
)

# Ignorar warnings de librerías externas
warnings.filterwarnings("ignore", category=SyntaxWarning)


def generate_segment(text: str) -> AudioSegment:
    """
    Genera un segmento de audio a partir de texto usando TTS.

    Parameters
    ----------
    text : str
        Texto a convertir en audio.

    Returns
    -------
    AudioSegment
        Segmento de audio generado.
    """

    tts = gTTS(text, lang="en", slow=False)

    buf = BytesIO()
    tts.write_to_fp(buf)
    buf.seek(0)

    return AudioSegment.from_file(buf, format="mp3")


def main() -> None:
    """
    Genera un audio compuesto por dos frases separadas por silencio.
    """

    print("🔊 Generando parte 1...")
    seg1 = generate_segment("This is the start of the analysis.")

    print("🔇 Generando silencio...")
    silence = AudioSegment.silent(duration=2500)

    print("🔊 Generando parte 2...")
    seg2 = generate_segment("And this is a completely separate segment after a pause.")

    full_audio = seg1 + silence + seg2

    output_file = "/content/english-editor/output/complex_audio.wav"

    output_dir = os.path.dirname(output_file)
    os.makedirs(output_dir, exist_ok=True)

    full_audio.export(output_file, format="wav")

    print(f"✅ Audio generado en: {output_file}")


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    main()
