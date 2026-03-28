
# @title 🧪 test_use_cases.py — [Fix Sintaxis] Suite Completa
# ✅ Test corregido (Sintaxis limpia): /content/english-editor/tests/modules/renderer/application/test_use_cases.py

# tests/modules/renderer/application/test_use_cases.py
"""
Tests para: use_cases.py
Responsabilidad: Validar la orquestación del padding (inferior y superior).
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

# === Imports del SUT ===
from english_editor.modules.renderer.application.use_cases import RenderMediaUseCase
from english_editor.modules.renderer.domain.ports.media_splicer import MediaSplicerPort
from english_editor.modules.renderer.domain.value_objects import MediaSegment


def test_render_media_should_orchestrate_padding_and_delegate_to_port():
    mock_splicer = Mock(spec=MediaSplicerPort)
    use_case = RenderMediaUseCase(splicer=mock_splicer)
    raw_segments = [{"start_ms": 1000.0, "end_ms": 5000.0}]
    padding_ms = 500.0

    use_case.execute(
        source_path=Path("in.mp4"),
        raw_segments=raw_segments,
        padding_ms=padding_ms,
        output_path=Path("out.mp4"),
    )

    call_kwargs = mock_splicer.splice_and_render.call_args.kwargs
    segment = call_kwargs["segments"][0]
    assert segment.start_ms == 500.0
    assert segment.end_ms == 5500.0


def test_render_media_should_fail_if_domain_validation_fails():
    mock_splicer = Mock(spec=MediaSplicerPort)
    use_case = RenderMediaUseCase(splicer=mock_splicer)
    invalid_segments = [{"start_ms": 5000.0, "end_ms": 1000.0}]

    with pytest.raises(ValueError):
        use_case.execute(Path("in.mp4"), invalid_segments, 0.0, Path("out.mp4"))

    mock_splicer.splice_and_render.assert_not_called()


def test_render_media_should_limit_padding_to_max_duration():
    mock_splicer = Mock(spec=MediaSplicerPort)
    use_case = RenderMediaUseCase(splicer=mock_splicer)
    raw_segments = [{"start_ms": 8000.0, "end_ms": 9900.0}]
    total_duration = 10000.0

    use_case.execute(
        source_path=Path("in.mp4"),
        raw_segments=raw_segments,
        padding_ms=500.0,
        output_path=Path("out.mp4"),
        media_duration_ms=total_duration,
    )

    call_kwargs = mock_splicer.splice_and_render.call_args.kwargs
    segment = call_kwargs["segments"][0]
    assert segment.end_ms == 10000.0


# A veces no quieres usar marcadores, sino probar un módulo específico en el que estás trabajando (por ejemplo, el de "orchestration")



