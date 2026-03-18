# tests/modules/renderer/infrastructure/test_adapters.py
"""
Tests para: adapters.py
Tipo: Unitario (Infraestructura Mockeada)
Arquitectura: AAA
Protocolos: Mocking de I/O OS (subprocess), Traducción de Excepciones.
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess

# === Imports del SUT e interfaces ===
from english_editor.modules.renderer.infrastructure.adapters import FFmpegMediaSplicer
from english_editor.modules.renderer.domain.ports.media_splicer import RenderExecutionError
from english_editor.modules.renderer.domain.value_objects import MediaSegment

# ==============================================================================
# === Casos de Prueba: FFmpegMediaSplicer ===
# ==============================================================================

@patch("english_editor.modules.renderer.infrastructure.adapters.subprocess.run")
@patch("english_editor.modules.renderer.infrastructure.adapters.Path.exists")
def test_ffmpeg_splicer_should_construct_correct_command_and_return_path(mock_exists, mock_run):
    """
    Given: Archivos válidos y una lista de segmentos.
    When:  Se ejecuta splice_and_render.
    Then:  Construye un comando ffmpeg con filter_complex y retorna la ruta de salida.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    mock_exists.return_value = True  # Simulamos que el archivo fuente existe
    mock_run.return_value = MagicMock(returncode=0) # Simulamos éxito de FFmpeg
    
    splicer = FFmpegMediaSplicer()
    source = Path("/fake/input.mp4")
    output = Path("/fake/output.mp4")
    segments = [
        MediaSegment(start_ms=0.0, end_ms=5000.0),      # 0 a 5s
        MediaSegment(start_ms=10000.0, end_ms=12000.0)  # 10s a 12s
    ]

    # ─── ACT ────────────────────────────────────────────────────────────────────
    result = splicer.splice_and_render(
        source_path=source,
        segments=segments,
        output_path=output
    )

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert result == output
    
    # Verificamos que se llamó a subprocess.run
    mock_run.assert_called_once()
    called_args = mock_run.call_args[0][0] # Obtenemos la lista de comandos
    
    # Validaciones clave del comando
    assert "ffmpeg" in called_args[0]
    assert "-i" in called_args
    assert str(source) in called_args
    assert "-filter_complex" in called_args
    assert str(output) in called_args

@patch("english_editor.modules.renderer.infrastructure.adapters.Path.exists")
def test_ffmpeg_splicer_should_raise_file_not_found_if_source_missing(mock_exists):
    """
    Given: Una ruta de archivo fuente que no existe en el disco.
    When:  Se ejecuta splice_and_render.
    Then:  Levanta FileNotFoundError inmediatamente antes de llamar a FFmpeg.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    mock_exists.return_value = False
    splicer = FFmpegMediaSplicer()

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    with pytest.raises(FileNotFoundError) as exc_info:
        splicer.splice_and_render(
            source_path=Path("/fake/missing.mp4"),
            segments=[MediaSegment(0.0, 1000.0)],
            output_path=Path("/fake/out.mp4")
        )
        
    error_msg = str(exc_info.value).lower()
    assert "no exist" in error_msg or "not found" in error_msg

@patch("english_editor.modules.renderer.infrastructure.adapters.subprocess.run")
@patch("english_editor.modules.renderer.infrastructure.adapters.Path.exists")
def test_ffmpeg_splicer_should_translate_subprocess_error_to_domain_error(mock_exists, mock_run):
    """
    Given: Un fallo interno de FFmpeg (ej: codec inválido).
    When:  Se ejecuta splice_and_render.
    Then:  Atrapa la excepción nativa y lanza RenderExecutionError (del Dominio).
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    mock_exists.return_value = True
    # Simulamos que FFmpeg crashea y lanza CalledProcessError
    mock_run.side_effect = subprocess.CalledProcessError(
        returncode=1, cmd="ffmpeg", stderr=b"Codec error"
    )
    
    splicer = FFmpegMediaSplicer()

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    with pytest.raises(RenderExecutionError) as exc_info:
        splicer.splice_and_render(
            source_path=Path("/fake/in.mp4"),
            segments=[MediaSegment(0.0, 1000.0)],
            output_path=Path("/fake/out.mp4")
        )
        
    error_msg = str(exc_info.value).lower()
    assert "fall" in error_msg or "error" in error_msg
