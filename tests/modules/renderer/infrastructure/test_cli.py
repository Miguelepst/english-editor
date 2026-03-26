
# @title 🧪 test_cli.py GateKeeperLocal(ok) — [Test] Adaptador Primario CLI
# ✅ CLI creado: /content/english-editor/src/english_editor/modules/renderer/infrastructure/cli.py
# ✅ Test del CLI creado: /content/english-editor/tests/modules/renderer/infrastructure/test_cli.py
# 🧪 Ejecutar test: cd english-editor && python -m pytest tests/modules/renderer/infrastructure/test_cli.py -v

# tests/modules/renderer/infrastructure/test_cli.py
"""
Tests para: cli.py
Tipo: Unitario (Adaptador Primario)
Arquitectura: AAA
Protocolos: Mocking del Caso de Uso, Parseo de Argumentos, Manejo de Salida.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# === Imports del SUT e interfaces ===
from english_editor.modules.renderer.infrastructure.cli import main, parse_args

# ==============================================================================
# === Casos de Prueba: CLI Parser y Main ===
# ==============================================================================


def test_cli_should_parse_arguments_correctly():
    test_args = [
        "--source",
        "input.mp4",
        "--output",
        "output.mp4",
        "--segments",
        "2.0,4.5",
        "10,15.5",
        "--padding",
        "500",
    ]
    args = parse_args(test_args)
    assert args.source == "input.mp4"
    assert args.output == "output.mp4"
    assert args.padding == 500.0
    assert args.segments == ["2.0,4.5", "10,15.5"]


@patch("english_editor.modules.renderer.infrastructure.cli.RenderMediaUseCase")
@patch("english_editor.modules.renderer.infrastructure.cli.FFmpegMediaSplicer")
def test_cli_main_should_convert_seconds_to_ms_and_execute_use_case(
    MockSplicer, MockUseCase
):
    mock_use_case_instance = MagicMock()
    MockUseCase.return_value = mock_use_case_instance
    mock_use_case_instance.execute.return_value = Path("output.mp4")

    test_args = [
        "cli.py",
        "-s",
        "input.mp4",
        "-o",
        "output.mp4",
        "-t",
        "2.0,4.0",
        "7.0,9.0",
        "-p",
        "500",
    ]

    with patch("sys.argv", test_args):
        main()

    mock_use_case_instance.execute.assert_called_once()
    call_kwargs = mock_use_case_instance.execute.call_args.kwargs
    assert call_kwargs["padding_ms"] == 500.0
    assert call_kwargs["raw_segments"] == [
        {"start_ms": 2000.0, "end_ms": 4000.0},
        {"start_ms": 7000.0, "end_ms": 9000.0},
    ]


@patch("english_editor.modules.renderer.infrastructure.cli.RenderMediaUseCase")
@patch("english_editor.modules.renderer.infrastructure.cli.FFmpegMediaSplicer")
def test_cli_main_should_handle_domain_errors_gracefully(
    MockSplicer, MockUseCase, capsys
):
    mock_use_case_instance = MagicMock()
    MockUseCase.return_value = mock_use_case_instance
    mock_use_case_instance.execute.side_effect = ValueError(
        "El inicio no puede ser negativo"
    )

    # ✅ AQUÍ ESTÁ EL CAMBIO CRÍTICO: "10.0,5.0" en lugar de "-1.0,5.0"
    test_args = ["cli.py", "-s", "in.mp4", "-o", "out.mp4", "-t", "10.0,5.0"]

    with pytest.raises(SystemExit) as exit_info:
        with patch("sys.argv", test_args):
            main()

    assert exit_info.value.code == 1
    captured = capsys.readouterr()
    assert "error" in captured.err.lower()
    assert "negativo" in captured.err.lower()



