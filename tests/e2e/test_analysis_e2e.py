
# @title 🧪 test_analysis_e2e.py — [E2E] Final Stable Version

# ✅ Test actualizado: /content/english-editor/tests/e2e/test_analysis_e2e.py

# tests/e2e/test_analysis_e2e.py
"""
Test End-to-End (E2E): Validación de Separación de Segmentos.

Estrategia: Frases Completas + Silencio Medio.
Usamos oraciones largas para asegurar que Whisper no haga "early exit"
y un silencio de 2s que fuerza la segmentación sin romper el contexto.
"""

import math
import os
import random
import struct
import wave
from pathlib import Path

import pytest

"""
# Facade Import
try:
    from english_editor.modules.analysis import (
        AnalyzeAudio,
        WhisperLocalAdapter,
        #TimeRange
        TimeRange,  # noqa: F401
    )
    DEPS_INSTALLED = True
except ImportError:
    DEPS_INSTALLED = False
"""

# === CONFIGURACIÓN: Detección robusta de dependencias externas ===
def _check_external_deps() -> bool:
    """
    Verifica que las librerías externas críticas para tests E2E estén instaladas.

    Returns:
        bool: True si todas las deps están disponibles, False en caso contrario.
    """
    try:
        # Dependencias directas del adapter WhisperLocalAdapter
        import librosa  # procesamiento de audio
        import torch  # backend de ML
        import whisper  # openai-whisper: modelo de transcripción

        # Validación opcional: verificar que whisper puede cargar un modelo mínimo
        # (descomentar si quieres ser más estricto, pero ralentiza la importación del test)
        # whisper.load_model("tiny", download_root="/tmp/whisper_cache", in_memory=True)

        return True
    except ImportError:
        return False
    except Exception:
        # Cualquier otro error (ej: CUDA sin GPU) también cuenta como "no disponible"
        return False

DEPS_INSTALLED = _check_external_deps()

# === Fixtures ===

@pytest.fixture
def pattern_audio_file(tmp_path):
    """
    Genera: [Frase 1] + [Silencio 2s] + [Frase 2]
    """
    filename = tmp_path / "e2e_split_pattern.wav"
    sample_rate = 16000

    try:
        from io import BytesIO

        from pydub import AudioSegment

        # from gtts import gTTS
        from english_editor.modules.audio_generation.infrastructure.adapters.edge_tts_adapter import (
            gTTS_edge as gTTS,
        )

        # Generador de ruido de fondo (Dither)
        def generate_silence(duration_ms):
            frames = int(sample_rate * (duration_ms / 1000.0))
            data = []
            for _ in range(frames):
                # Dither +/- 2 para evitar ceros absolutos
                val = random.randint(-2, 2)
                data.append(struct.pack("<h", val))

            noise_io = BytesIO()

            with wave.open(noise_io, "w") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                wav.writeframes(b"".join(data))

            # with wave.open(noise_io, 'w') as wav:
            #    wav.setnchannels(1); wav.setsampwidth(2); wav.setframerate(sample_rate)
            #    wav.writeframes(b''.join(data))

            noise_io.seek(0)
            return AudioSegment.from_wav(noise_io)

        # 1. Silencio Intermedio "Goldilocks" (2.0s)
        # Menos de 1.5s -> Whisper suele unir.
        # Más de 3.0s -> Whisper suele abandonar (early exit).
        gap_duration = 2000
        silence_gap = generate_silence(gap_duration)
        silence_pad = generate_silence(500)  # Padding corto

        def text_to_audio(text):
            # Usamos frases completas para mantener la atención del modelo
            tts = gTTS(text, lang="en", slow=False)
            buf = BytesIO()
            tts.write_to_fp(buf)
            buf.seek(0)
            seg = AudioSegment.from_file(buf, format="mp3")
            return seg.set_frame_rate(sample_rate).set_channels(1)

        print("🔊 Generando Frases...")
        # Frases largas = Mayor probabilidad logarítmica = Menor chance de ser ignoradas
        voice_1 = text_to_audio("This is the first segment of the test.")
        voice_2 = text_to_audio("And now we are recording the second part.")

        # Concatenar
        full_audio = silence_pad + voice_1 + silence_gap + voice_2 + silence_pad

        full_audio.export(
            str(filename), format="wav", parameters=["-ar", str(sample_rate)]
        )

        print(
            f"✅ Audio generado: {len(full_audio) / 1000:.2f}s (Gap: {gap_duration / 1000}s)"
        )

    except ImportError:
        with open(filename, "wb") as f:
            f.write(b"RIFF")

    # except ImportError:
    #    with open(filename, 'wb') as f: f.write(b'RIFF')

    return filename

# === Test ===

@pytest.mark.e2e
@pytest.mark.skipif(not DEPS_INSTALLED, reason="Faltan dependencias")
def test_e2e_separation_of_segments(pattern_audio_file):
    # ─── IMPORTS LOCALES (solo si el test se ejecuta) ─────────────────────
    from english_editor.modules.analysis.application.use_cases import AnalyzeAudio
    from english_editor.modules.analysis.domain.value_objects import TimeRange
    from english_editor.modules.analysis.infrastructure.whisper_adapter import (
        WhisperLocalAdapter,
    )
    # ─────────────────────────────────────────────────────────────────────

    # 1. Setup
    print("⚙️  [E2E] Inicializando Whisper (base.en)...")
    adapter = WhisperLocalAdapter(model_size="base.en")
    use_case = AnalyzeAudio(engine=adapter)

    # 2. Execution
    print("🚀 [E2E] Analizando...")
    segments = use_case.execute(pattern_audio_file)
    print(f"📊 [E2E] Resultado raw: {segments}")

    # 3. Assertions

    # Si devuelve 1 segmento, analizamos por qué
    if len(segments) == 1:
        seg = segments[0]

        # Obtenemos duración real del archivo
        import wave

        with wave.open(str(pattern_audio_file), "rb") as f:
            file_dur = f.getnframes() / f.getframerate()

        print(
            f"⚠️ Un solo segmento detectado: {seg.start:.2f}s -> {seg.end:.2f}s (Total Audio: {file_dur:.2f}s)"
        )

        # Si el segmento cubre TODO el audio (start cerca de 0, end cerca del final)
        # Significa que FALLÓ en separar (merged).
        if seg.end > (file_dur - 1.5):
            pytest.fail(
                "Fallo: El modelo fusionó las dos frases ignorando el silencio de 2s."
            )
        else:
            # Si el segmento termina a la mitad, es 'Early Exit'.
            # Nota: Esto a veces pasa en CI/CD lento. Podemos ser permisivos o fallar.
            # Para este test, vamos a fallar porque queremos garantizar robustness.
            pytest.fail(
                f"Fallo: Early Exit. El modelo dejó de escuchar a los {seg.end}s y el audio dura {file_dur}s"
            )

    # Caso ideal: 2 o más segmentos
    assert len(segments) >= 2, "Debe detectar al menos 2 segmentos."

    # Verificar que hay un hueco entre el segmento 1 y el 2
    # Buscamos el mayor hueco entre segmentos consecutivos
    max_gap = 0
    for i in range(len(segments) - 1):
        current_gap = segments[i + 1].start - segments[i].end
        if current_gap > max_gap:
            max_gap = current_gap

    print(f"🔍 Mayor silencio detectado entre frases: {max_gap:.2f}s")

    # El silencio real es 2.0s. Whisper suele "comerse" un poco los bordes.
    # Un gap detectado de > 0.5s prueba que NO están pegados.
    assert max_gap > 0.5, (
        f"Fallo: Los segmentos están demasiado pegados (Gap: {max_gap}s)."
    )

    print("✅ [E2E] Éxito: Frases correctamente separadas.")


