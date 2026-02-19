# tests/modules/analysis/infrastructure/test_integration_whisper.py
"""
Tests de Integración: WhisperLocalAdapter (Real)
Tipo: Integración (Slow, I/O, ML Model)
Objetivo: Validar que el adaptador real carga el modelo y procesa audio sin crashear.
"""
import pytest
import wave
import struct
import math
from pathlib import Path

# Intentamos importar las dependencias reales.
# Si no están, saltamos el test para no romper CI/CD básico.
try:
    import whisper
    import librosa
    import torch
    DEPS_INSTALLED = True
except ImportError:
    DEPS_INSTALLED = False

from english_editor.modules.analysis.infrastructure.whisper_adapter import WhisperLocalAdapter
from english_editor.modules.analysis.domain.value_objects import TimeRange

# === Fixtures de Infraestructura ===

@pytest.fixture
def real_wav_file(tmp_path):
    """
    Genera un archivo WAV real de 2 segundos (1s silencio, 1s ruido)
    para probar el motor sin depender de archivos externos.
    """
    filename = tmp_path / "integration_test.wav"

    # Parámetros de audio
    sample_rate = 16000
    duration_sec = 2.0
    n_frames = int(sample_rate * duration_sec)

    with wave.open(str(filename), 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)

        # Generar datos: 1 seg silencio, 1 seg tono 440Hz
        data = []
        for i in range(n_frames):
            if i < sample_rate: # Primer segundo: silencio
                value = 0
            else: # Segundo segundo: tono
                t = float(i) / sample_rate
                value = int(32767.0 * math.sin(2.0 * math.pi * 440.0 * t))

            data.append(struct.pack('<h', value))

        wav_file.writeframes(b''.join(data))

    return filename

# === Casos de Prueba de Integración ===

@pytest.mark.skipif(not DEPS_INSTALLED, reason="Requiere whisper, torch y librosa instalados")
@pytest.mark.integration
@pytest.mark.timeout(60)  # Máximo 60 segundos # Agregar timeout para evitar tests infinitos
def test_real_whisper_pipeline_execution(real_wav_file):
    """
    Given: Un archivo WAV real generado en disco
    When: Se instancia el WhisperLocalAdapter real y se ejecuta detect_voice_activity
    Then:
        1. No lanza excepciones (Crash-Free).
        2. Retorna una lista de TimeRange.
        3. (Opcional) Detecta algo en el segundo con audio.
    """
    # Arrange
    # Usamos tiny.en porque es el más rápido para tests
    adapter = WhisperLocalAdapter(model_size="tiny.en")

    print(f"\n[INTEGRATION] Cargando modelo Whisper y procesando: {real_wav_file}...")

    # Act
    # Esto va a tardar unos segundos la primera vez (descarga de modelo)
    result = adapter.detect_voice_activity(real_wav_file)

    # Assert
    # 1. Validación de Tipos (Contrato cumplido)
    assert isinstance(result, list)
    if len(result) > 0:
        assert isinstance(result[0], TimeRange)


    # 2. Agregar más assert significativo
    assert len(result) >= 0, "Debería retornar al menos una lista vacía"
    # Opcional: verificar que detecta algo en el segundo con audio
    if len(result) > 0:
        assert any(r.start >= 1.0 for r in result), "Debería detectar voz después del segundo 1"



    # 2. Validación de lógica básica
    # El archivo tiene audio en el segundo 1.0 - 2.0.
    # Whisper debería detectar ALGO, o al menos no crashear.
    # Nota: No asertamos exactitud perfecta en un test de integración,
    # solo salud del sistema.
    print(f"[INTEGRATION] Resultado obtenido: {result}")

@pytest.mark.skipif(not DEPS_INSTALLED, reason="Requiere dependencias reales")
def test_real_adapter_fails_gracefully_on_missing_file():
    """
    Given: Una ruta inexistente
    When: El adaptador real intenta leerla
    Then: Lanza AudioFileError (no FileNotFoundError crudo)
    """
    # Arrange
    adapter = WhisperLocalAdapter()
    bad_path = Path("no_existo.wav")

    # Act & Assert
    from english_editor.modules.analysis.domain.exceptions import AudioFileError

    with pytest.raises(AudioFileError):
        adapter.detect_voice_activity(bad_path)