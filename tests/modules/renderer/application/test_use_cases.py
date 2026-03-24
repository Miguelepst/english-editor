# tests/modules/renderer/application/test_use_cases.py
"""
Tests para: use_cases.py
Tipo: Unitario
Arquitectura: AAA (Arrange-Act-Assert) + Given-When-Then
Protocolos: Orquestación, Inyección de Dependencias, Mocking estricto de puertos.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock

# === Imports del SUT (System Under Test) e interfaces ===
from english_editor.modules.renderer.application.use_cases import RenderMediaUseCase
from english_editor.modules.renderer.domain.ports.media_splicer import MediaSplicerPort
from english_editor.modules.renderer.domain.value_objects import MediaSegment

# ==============================================================================
# === Casos de Prueba: RenderMediaUseCase ===
# ==============================================================================

def test_render_media_should_orchestrate_padding_and_delegate_to_port():
    """
    Given: Datos crudos válidos de segmentos y un padding configurado.
    When:  Se ejecuta el caso de uso.
    Then:  Convierte a entidades de dominio, aplica el padding matemáticamente
           y delega la ejecución al puerto inyectado con los segmentos alterados.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    # 1. Mock estricto del Puerto (Infraestructura)
    mock_splicer = Mock(spec=MediaSplicerPort)
    expected_output = Path("/fake/output_editado.mp4")
    mock_splicer.splice_and_render.return_value = expected_output

    # 2. Instanciación del Caso de Uso inyectando la dependencia
    use_case = RenderMediaUseCase(splicer=mock_splicer)

    # 3. Datos de entrada (Simulando lo que llega de un controlador/API)
    source = Path("/fake/original.mp4")
    dest = Path("/fake/output_editado.mp4")
    raw_segments = [
        {"start_ms": 1000.0, "end_ms": 5000.0},  # Duración 4s
        {"start_ms": 10000.0, "end_ms": 15000.0} # Duración 5s
    ]
    padding_ms = 500.0 # Medio segundo de margen

    # ─── ACT ────────────────────────────────────────────────────────────────────
    result = use_case.execute(
        source_path=source,
        raw_segments=raw_segments,
        padding_ms=padding_ms,
        output_path=dest
    )

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    # 1. Verifica el retorno
    assert result == expected_output

    # 2. Verifica que el puerto fue llamado exactamente una vez
    mock_splicer.splice_and_render.assert_called_once()

    # 3. Extrae los argumentos con los que se llamó al puerto para verificar la orquestación
    call_kwargs = mock_splicer.splice_and_render.call_args.kwargs
    assert call_kwargs["source_path"] == source
    assert call_kwargs["output_path"] == dest
    
    # 4. Verifica que la lógica de negocio (padding) se delegó al dominio y llegó al puerto
    processed_segments = call_kwargs["segments"]
    assert len(processed_segments) == 2
    assert isinstance(processed_segments[0], MediaSegment)
    
    # Segmento 1: 1000 a 5000 con 500ms de padding -> 500 a 5500
    assert processed_segments[0].start_ms == 500.0
    assert processed_segments[0].end_ms == 5500.0
    
    # Segmento 2: 10000 a 15000 con 500ms de padding -> 9500 a 15500
    assert processed_segments[1].start_ms == 9500.0
    assert processed_segments[1].end_ms == 15500.0

def test_render_media_should_fail_if_domain_validation_fails():
    """
    Given: Datos crudos inválidos (inicio mayor que fin).
    When:  Se ejecuta el caso de uso.
    Then:  El error de dominio se propaga ANTES de llamar al puerto.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    mock_splicer = Mock(spec=MediaSplicerPort)
    use_case = RenderMediaUseCase(splicer=mock_splicer)
    
    invalid_raw_segments = [{"start_ms": 5000.0, "end_ms": 1000.0}] # Inválido

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    with pytest.raises(ValueError) as exc_info:
        use_case.execute(
            source_path=Path("/fake/in.mp4"),
            raw_segments=invalid_raw_segments,
            padding_ms=0.0,
            output_path=Path("/fake/out.mp4")
        )

    # Validamos usando la regla de interpolación (palabras clave)
    error_msg = str(exc_info.value).lower()
    assert "start_ms" in error_msg
    assert "end_ms" in error_msg
    
    # Garantizamos que la infraestructura nunca se tocó si el dominio falló
    mock_splicer.splice_and_render.assert_not_called()
