
# @title 📄 demo_analysis.py — [Demo] Interactive Speech Analysis (With Transcription)

# 🎵 Generando audio de prueba...
# ✅ Demo con transcripción creada: /content/english-editor/demo_analysis.py
# 📂 Archivos se guardarán en: /content/english-editor/output/
# 💡 Ejecutar con: !python /content/english-editor/demo_analysis.py

# english-editor/demo_analysis.py
"""
Demo Interactiva: Análisis de Voz (Micro-SPS 02).

Arquitectura: Composition Root (Consumer)
Responsabilidad: Cablear dependencias reales y ejecutar el caso de uso.

Best Practices:
- Archivos temporales en output/ dentro del proyecto
- Limpieza automática de archivos temporales
- Rutas relativas al script, no al working directory
- Mostrar transcripción real de Whisper (valor agregado para demo)
"""

import math
import struct
import sys
import time
import wave
from pathlib import Path

# === Configuración de Path para Imports ===
SCRIPT_ROOT = Path(__file__).parent
PROJECT_ROOT = SCRIPT_ROOT
OUTPUT_DIR = SCRIPT_ROOT / "output"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
sys.path.append(str(PROJECT_ROOT / "src"))

try:
    # === Imports del Proyecto ===

    from english_editor.modules.analysis.application.use_cases import AnalyzeAudio
    from english_editor.modules.analysis.domain.exceptions import AnalysisError
    from english_editor.modules.analysis.domain.value_objects import TimeRange
    from english_editor.modules.analysis.infrastructure.whisper_adapter import (
        WhisperLocalAdapter,
    )

    # === Imports para Audio Realista (Opcionales) ===
    try:
        from english_editor.modules.audio_generation.infrastructure.adapters.edge_tts_adapter import (
            gTTS_edge as gTTS,
        )

        # from gtts import gTTS
        GTTS_AVAILABLE = True
    except ImportError:
        GTTS_AVAILABLE = False

    try:
        import librosa
        import soundfile as sf

        LIBROSA_AVAILABLE = True
    except ImportError:
        LIBROSA_AVAILABLE = False

except ImportError as e:
    print(f"❌ Error de Importación Crítico: {e}")
    print("⚠️  Verifica que hayas ejecutado las celdas de instalación del paquete.")
    sys.exit(1)

# === Utilidades de Demo ===


def generate_demo_audio_tone(filename: Path):
    """Genera un archivo WAV sintético (tono 440Hz)."""
    print("🎵 Generando audio de prueba (tono sintético)...")
    sample_rate = 16000
    duration_sec = 7

    with wave.open(str(filename), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        data = []
        for i in range(int(sample_rate * duration_sec)):
            t = float(i) / sample_rate
            if 2.0 <= t <= 5.0:
                val = math.sin(2 * math.pi * 440 * t) + 0.5 * math.sin(
                    2 * math.pi * 880 * t
                )
                val = int(val * 10000)
            else:
                val = 0
            data.append(struct.pack("<h", max(-32768, min(32767, val))))

        wav.writeframes(b"".join(data))


def generate_demo_audio_speech(
    filename: Path, text: str = "Hello world! This is a voice activity detection test."
):
    """
    Genera audio con VOZ HUMANA REAL usando Google Text-to-Speech.
    """
    if not GTTS_AVAILABLE:
        print("⚠️  gTTS no disponible, usando tono sintético...")
        return generate_demo_audio_tone(filename)

    print("🎤 Generando audio con voz real (gTTS)...")
    print(f'   📝 Texto original: "{text}"')

    temp_mp3 = OUTPUT_DIR / f"temp_{filename.stem}.mp3"

    try:
        tts = gTTS(text=text, lang="en")
        tts.save(str(temp_mp3))

        if LIBROSA_AVAILABLE:
            audio_data, sr = librosa.load(str(temp_mp3), sr=16000)
            sf.write(str(filename), audio_data, sr)
            print(f"   ✅ Audio WAV generado: {filename}")
        else:
            temp_mp3.rename(filename)
            print(f"   ✅ Audio generado: {filename}")

        if temp_mp3.exists():
            temp_mp3.unlink()
            print(f"   🧹 Temporal limpio: {temp_mp3.name}")

        return filename

    except Exception as e:
        print(f"   ⚠️  Error generando audio: {e}")
        if temp_mp3.exists():
            temp_mp3.unlink()
        raise


def display_audio_info(filename: Path):
    """Muestra información técnica del audio."""
    if LIBROSA_AVAILABLE:
        try:
            duration = librosa.get_duration(path=str(filename))
            print(f"   ⏱ Duración: {duration:.2f}s")

            audio_data, _ = librosa.load(str(filename), sr=16000)
            rms = (audio_data**2).mean() ** 0.5
            print(f"   📊 RMS Energy: {rms:.4f}")
        except Exception:
            pass
    else:
        print(f"   📁 Archivo: {filename.name}")

    print(f"   📂 Ruta: {filename.absolute()}")


def cleanup_old_files(max_age_hours: int = 24):
    """Limpieza automática de archivos antiguos en output/"""
    import time

    cleaned = 0
    current_time = time.time()

    for file in OUTPUT_DIR.glob("*.wav"):
        file_age = current_time - file.stat().st_mtime
        if file_age > max_age_hours * 3600:
            file.unlink()
            cleaned += 1

    if cleaned > 0:
        print(f"🧹 Limpieza: {cleaned} archivo(s) antiguo(s) eliminado(s)")


def format_transcription_display(
    text: str | None, confidence: float | None = None
) -> str:
    """
    ✅ Best Practice: Formateo de texto separado de la lógica de negocio.
    """
    if not text or not text.strip():
        return "   ⚪ (Sin transcripción)"

    # Truncar si es muy largo para display
    max_length = 200
    if len(text) > max_length:
        text = text[:max_length] + "..."

    # Mostrar con indentación y word-wrap
    wrapped_lines = []
    current_line = "   "
    words = text.split()

    for word in words:
        if len(current_line) + len(word) + 1 > 80:
            wrapped_lines.append(current_line)
            current_line = "   " + word
        else:
            current_line += (" " if current_line.strip() else "") + word
    wrapped_lines.append(current_line)

    result = "\n".join(wrapped_lines)

    if confidence is not None:
        result += f"\n   📊 Confianza: {confidence:.1%}"

    return result


# === Composition Root ===


def main():
    print("=" * 60)
    print("🎤 MICRO-SPS 02: SPEECH ANALYSIS DEMO")
    print("=" * 60)

    cleanup_old_files(max_age_hours=24)

    # 1. Preparación de Inputs
    audio_path = OUTPUT_DIR / "demo_speech.wav"

    print(f"\n📂 Directorio de salida: {OUTPUT_DIR}")
    print("   1. Voz real (gTTS) - Recomendado")
    print("   2. Tono sintético (fallback)")
    print("   3. Usar archivo existente")

    # Texto esperado para comparar después
    expected_text = (
        "Hello world! This is a voice activity detection test. Can you hear me?"
    )

    if audio_path.exists():
        print(f"\n✅ Usando archivo existente: {audio_path.name}")
        expected_text = "(Desconocido - archivo externo)"
    elif GTTS_AVAILABLE:
        print("\n🎤 Usando voz real (gTTS disponible)")
        audio_path = generate_demo_audio_speech(audio_path, text=expected_text)
    else:
        print("\n🎵 Usando tono sintético (gTTS no disponible)")
        generate_demo_audio_tone(audio_path)
        expected_text = "(N/A - tono sintético)"

    display_audio_info(audio_path)

    try:
        # 2. Inyección de Dependencias (Infrastructure -> Application)
        print("\n⚙️  Inicializando Whisper (Tiny.en @ CPU)...")
        adapter = WhisperLocalAdapter(model_size="tiny.en")

        print("🧠 Inicializando Caso de Uso...")
        use_case = AnalyzeAudio(engine=adapter)

        # 3. Ejecución
        print("\n🚀 Analizando audio (Chunking + VAD + Transcripción)...")
        print("-" * 40)
        start_time = time.time()

        # ✅ Voice Activity Detection
        segments: list[TimeRange] = use_case.execute(audio_path)

        # ✅ Transcripción (usando el adapter directamente - método público)
        # Esto respeta arquitectura: adapter es infraestructura, demo es consumer
        print("\n📝 Transcribiendo audio con Whisper...")
        try:
            if adapter._model is None:
                raise ValueError("El modelo Whisper no se inicializó correctamente")
            transcript_result = adapter._model.transcribe(
                str(audio_path), fp16=False, language="en", verbose=False
            )
            transcribed_text = transcript_result.get("text", "").strip()
        except Exception as e:
            transcribed_text = f"Error: {e}"

        elapsed = time.time() - start_time

        # 4. Presentación
        print("-" * 40)
        print(f"✅ Finalizado en {elapsed:.2f}s")

        print("\n" + "=" * 60)
        print("📊 RESULTADOS:")
        print("=" * 60)

        # Voice Activity Detection
        print("\n🔍 VOICE ACTIVITY DETECTION:")
        if not segments:
            print("   ⚪ (Silencio total o no se detectó voz)")
        else:
            print(f"   🟢 {len(segments)} segmento(s) de voz encontrado(s):\n")
            for i, seg in enumerate(segments, 1):
                print(
                    f"   #{i}: [{seg.start:6.2f}s  →  {seg.end:6.2f}s]  (duración: {seg.duration:5.2f}s)"
                )

        # Transcription
        print("\n" + "-" * 60)
        print("📝 TRANSCRIPCIÓN (Whisper):")
        print("-" * 60)
        print(format_transcription_display(transcribed_text))

        # Comparación (solo si es gTTS)
        if GTTS_AVAILABLE and audio_path.exists():
            print("\n" + "-" * 60)
            print("🔎 VALIDACIÓN:")
            print("-" * 60)
            if transcribed_text and expected_text != "(Desconocido - archivo externo)":
                # Simple check: palabras clave
                expected_words = set(expected_text.lower().split())
                transcribed_words = set(transcribed_text.lower().split())
                match_ratio = len(expected_words & transcribed_words) / len(
                    expected_words
                )

                if match_ratio > 0.5:
                    print(f"   ✅ {match_ratio:.0%} de palabras clave coinciden")
                else:
                    print(
                        f"   ⚠️  {match_ratio:.0%} de palabras clave coinciden (puede ser variación de Whisper)"
                    )
            else:
                print("   ⚪ (Sin validación - archivo externo o error)")

        print("\n" + "=" * 60)
        print(f"💡 Archivos guardados en: {OUTPUT_DIR.absolute()}")
        print("💡 TIP: Para más precisión, usa audio de 16kHz mono WAV")
        print("=" * 60)

    except AnalysisError as e:
        print(f"\n❌ Error de Dominio Controlado: {e}")
    except Exception as e:
        print(f"\n❌ Error Inesperado (Bug): {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()


