# tests/performance/test_benchmark_whisper.py
"""
Tests para: benchmark_whisper.py
Tipo: Performance (No Funcional / Benchmarking)
Arquitectura: AAA (Arrange-Act-Assert) + Given-When-Then
Protocolos: Aislamiento, Monitoreo de Recursos (RAM/CPU), Benchmarking de Tiempo
"""

import pytest
import sys
import wave
import os
import threading
import time
import psutil
from pathlib import Path

# === 🧪 Protocolos de Calidad Obligatorios ===
# 🔒 DOMINIO PURO: Tests sin I/O ni mocks. Solo lógica de negocio.
# 🧪 AISLAMIENTO: Cada test es independiente (no comparte estado con otros tests).
# ⚡ VELOCIDAD: Tests unitarios < 100ms. Tests lentos marcar con @pytest.mark.slow.
# 🔤 DETERMINISMO: Sin aleatoriedad sin seed controlado.
# 🚫 SIN EFECTOS SECUNDARIOS: Nunca escribir en filesystem real (usar tmp_path fixture).
# 🌐 SIN DEPENDENCIAS EXTERNAS: Mockear APIs, redes, bases de datos en tests unitarios.

# === Configuración de Rutas (Path Patching) ===
PROJECT_ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT_DIR / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.append(str(SRC_PATH))

# === Imports del SUT (System Under Test) ===
from english_editor.modules.analysis.infrastructure.whisper_adapter import (
    WhisperLocalAdapter,
)


# === CONFIGURACIÓN: Detección de dependencias para tests de performance ===
def _check_performance_deps() -> bool:
    """
    Verifica que las librerías necesarias para benchmarks de Whisper estén instaladas.

    Returns:
        bool: True si todas las deps están disponibles, False en caso contrario.
    """
    try:
        import whisper  # openai-whisper
        import librosa  # procesamiento de audio
        import torch  # backend de ML
        import psutil  # monitoreo de recursos (ya lo usas en ResourceMonitor)

        return True
    except ImportError:
        return False
    except Exception:
        return False


# Skip automático si faltan dependencias críticas
pytestmark = [
    pytest.mark.performance,
    pytest.mark.skipif(
        not _check_performance_deps(),
        reason="Requiere whisper, librosa, torch y psutil instalados",
    ),
]

# pytestmark = pytest.mark.performance

# === Utilidades y Monitores (Sin Regresión) ===
TEST_DURATION_MINUTES = 1  # 1 min para el benchmark
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
                mem_info = self.process.memory_info()
                ram_mb = mem_info.rss / 1024 / 1024
                self.peak_ram_mb = max(self.peak_ram_mb, ram_mb)
                self.cpu_usage_samples.append(self.process.cpu_percent(interval=None))
            except Exception:
                pass
            time.sleep(self.interval)

    def stop(self):
        self.stop_event.set()


def generate_stress_audio(filename: Path, duration_min: int):
    """Genera un WAV largo con ruido blanco."""
    total_frames = int(SAMPLE_RATE * duration_min * 60)
    with wave.open(str(filename), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        block_frames = 1024 * 1024
        frames_written = 0
        while frames_written < total_frames:
            current_block = min(block_frames, total_frames - frames_written)
            data = os.urandom(current_block * 2)
            wav.writeframes(data)
            frames_written += current_block


# === Casos de Prueba ===


def test_whisper_engine_should_process_audio_within_benchmark_limits(
    benchmark, tmp_path
):
    """
    Given: Un archivo de audio de estrés generado y el adaptador Whisper inicializado.
    When:  Se ejecuta la detección de actividad de voz midiendo con el fixture 'benchmark'.
    Then:  El resultado es válido y el consumo de RAM no excede el límite permitido.

    Regla de negocio validada: DR-03 Límite de Memoria y Rendimiento
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    # audio_path = Path("stress_test.wav")       # ← Ruta relativa, puede colisionar
    audio_path = (
        tmp_path / "stress_test.wav"
    )  # ← Aislado por pytest, se limpia automático
    if not audio_path.exists():
        generate_stress_audio(audio_path, TEST_DURATION_MINUTES)

    monitor = ResourceMonitor()
    adapter = WhisperLocalAdapter(model_size="tiny.en")

    monitor.start()

    # ─── ACT ────────────────────────────────────────────────────────────────────
    try:
        # benchmark.pedantic nos permite controlar exactamente cuántas veces se ejecuta
        # para que no repita el análisis del audio infinito número de veces.
        result = benchmark.pedantic(
            adapter.detect_voice_activity, args=(audio_path,), iterations=1, rounds=1
        )
    finally:
        monitor.stop()
        monitor.join()

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert result is not None, "El adaptador debe devolver un resultado válido"

    # Verificamos la RAM usando el monitor original
    assert (
        monitor.peak_ram_mb < 5000.0
    ), f"Consumo de RAM excedido: {monitor.peak_ram_mb}MB > 5000MB"

    # Limpieza
    if audio_path.exists():
        os.remove(audio_path)
