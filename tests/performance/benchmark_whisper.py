# tests/performance/benchmark_whisper.py
"""
Benchmark de Rendimiento: Speech Analysis Engine.
"""

import sys
import time
import wave
import struct
import threading
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.performance

# === Configuración de Rutas (Path Patching) ===
# Calculamos la raíz del proyecto para importar 'src'
# Archivo en: tests/performance/benchmark_whisper.py
# Root en:    ../../..
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

try:
    import psutil
    from english_editor.modules.analysis.infrastructure.whisper_adapter import (
        WhisperLocalAdapter,
    )

    # from english_editor.modules.analysis.domain.exceptions import MemoryLimitExceeded
    from english_editor.modules.analysis.domain.exceptions import (
        MemoryLimitExceeded,  # noqa: F401
    )

    # from english_editor.modules.analysis.domain.exceptions import MemoryLimitExceeded  # noqa: F401  # error de esta forma
except ImportError as e:
    print(f"❌ Error de Dependencias: {e}")
    print("💡 Asegúrate de instalar: pip install psutil openai-whisper torch librosa")
    sys.exit(1)

# === Configuración del Test ===
TEST_DURATION_MINUTES = 2  # Reducido a 2 min para feedback rápido en la corrección
SAMPLE_RATE = 16000


class ResourceMonitor(threading.Thread):
    """Monitorea RAM y CPU en segundo plano."""

    def __init__(self, interval=0.1):
        super().__init__()
        self.interval = interval
        self.stop_event = threading.Event()
        self.peak_ram_mb = 0.0
        self.cpu_usage_samples = []
        self.process = psutil.Process(os.getpid())

    def run(self):
        while not self.stop_event.is_set():
            try:
                # RAM en MB (RSS)
                mem_info = self.process.memory_info()
                ram_mb = mem_info.rss / 1024 / 1024
                self.peak_ram_mb = max(self.peak_ram_mb, ram_mb)

                # CPU Porcentaje
                self.cpu_usage_samples.append(self.process.cpu_percent(interval=None))
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self.stop_event.set()


def generate_stress_audio(filename: Path, duration_min: int):
    """Genera un WAV largo con ruido blanco."""
    print(f"🔨 Generando audio de estrés ({duration_min} min) en: {filename}")
    total_frames = int(SAMPLE_RATE * duration_min * 60)

    with wave.open(str(filename), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)

        # Escribir en bloques de 1MB para no saturar memoria
        block_frames = 1024 * 1024
        frames_written = 0

        while frames_written < total_frames:
            current_block = min(block_frames, total_frames - frames_written)
            # Ruido blanco (bytes aleatorios)
            data = os.urandom(current_block * 2)
            wav.writeframes(data)
            frames_written += current_block


def main():
    print("=" * 60)
    print("🚀 PERFORMANCE BENCHMARK: WHISPER ENGINE")
    print("=" * 60)

    # 1. Setup
    audio_path = Path("stress_test.wav")
    if not audio_path.exists():
        generate_stress_audio(audio_path, TEST_DURATION_MINUTES)

    # 2. Inicializar Monitor
    monitor = ResourceMonitor()
    print("⚙️  Cargando modelo...")
    adapter = WhisperLocalAdapter(model_size="tiny.en")

    print(f"\n⏱️  Procesando audio...")
    start_time = time.time()
    monitor.start()

    try:
        # 3. Ejecución Crítica
        # segments = adapter.detect_voice_activity(audio_path)  #rufus error

        # ✅ DESPUÉS
        _ = adapter.detect_voice_activity(
            audio_path
        )  # Usar _ para indicar que es intencional

        end_time = time.time()
        elapsed = end_time - start_time

    except Exception as e:
        print(f"\n❌ CRASH DURANTE BENCHMARK: {e}")
        # Imprimir traceback para debug
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        monitor.stop()
        monitor.join()

    # 4. Análisis de Resultados
    audio_duration_sec = TEST_DURATION_MINUTES * 60
    rtf = elapsed / audio_duration_sec
    avg_cpu = (
        sum(monitor.cpu_usage_samples) / len(monitor.cpu_usage_samples)
        if monitor.cpu_usage_samples
        else 0
    )

    print("\n" + "=" * 60)
    print("📈 REPORTE DE RENDIMIENTO")
    print("=" * 60)
    print(f"• Audio Procesado:     {TEST_DURATION_MINUTES} min")
    print(f"• Tiempo de Ejecución: {elapsed:.2f} seg")
    print("-" * 40)
    print(f"• Consumo RAM Pico:    {monitor.peak_ram_mb:.2f} MB")
    print(f"• Límite (DR-03):      5000.00 MB")
    print(
        f"• Estado RAM:          {'✅ PASS' if monitor.peak_ram_mb < 5000 else '❌ FAIL'}"
    )
    print("-" * 40)
    print(f"• RTF:                 {rtf:.3f}x")
    print(f"• CPU Promedio:        {avg_cpu:.1f}%")
    print("=" * 60)

    # Limpieza
    if audio_path.exists():
        os.remove(audio_path)


if __name__ == "__main__":
    main()
