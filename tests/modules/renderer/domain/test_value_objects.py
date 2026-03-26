
#@title 🧪 test_value_objects.py — [Test] Actualizado (Protección Bidireccional)
# tests/modules/renderer/domain/test_value_objects.py
"""
Tests para: value_objects.py
Tipo: Unitario
Arquitectura: AAA (Arrange-Act-Assert) + Given-When-Then
Protocolos: Pureza de dominio, Aislamiento, Determinismo
"""

import pytest

# === 🧪 Protocolos de Calidad Obligatorios ===
# 🔒 DOMINIO PURO: Tests sin I/O ni mocks. Solo lógica de negocio.
# 🔤 DETERMINISMO: Sin aleatoriedad sin seed controlado.
# === Imports del SUT (System Under Test) ===
# Nota: Importamos asumiendo la existencia (TDD).
# Python 3.12 syntax native.
from english_editor.modules.renderer.domain.value_objects import MediaSegment, Padding

# ==============================================================================
# === Casos de Prueba: Padding ===
# ==============================================================================


def test_padding_should_initialize_with_valid_duration():
    """
    Given: Una duración de padding válida en milisegundos.
    When:  Se instancia el objeto Padding.
    Then:  El objeto se crea y almacena el valor correctamente.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    valid_ms = 1500.5

    # ─── ACT ────────────────────────────────────────────────────────────────────
    padding = Padding(duration_ms=valid_ms)

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert padding.duration_ms == valid_ms


def test_padding_should_reject_negative_duration():
    """
    Given: Un intento de crear Padding con duración negativa.
    When:  Se instancia el objeto.
    Then:  Levanta ValueError.
    Regla: DR-01/04 Padding no puede retroceder el tiempo negativamente como valor absoluto.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    invalid_ms = -500.0

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    with pytest.raises(ValueError) as exc_info:
        Padding(duration_ms=invalid_ms)

    # Validación robusta (Regla A.1): Palabras clave, no frases completas
    error_msg = str(exc_info.value).lower()
    assert "duration_ms" in error_msg
    assert "negativ" in error_msg


# ==============================================================================
# === Casos de Prueba: MediaSegment ===
# ==============================================================================


def test_media_segment_should_calculate_duration_correctly():
    """
    Given: Un segmento con inicio en 10.0s y fin en 25.5s.
    When:  Se consulta su propiedad de duración.
    Then:  Retorna 15.5s.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    segment = MediaSegment(start_ms=10000.0, end_ms=25500.0)

    # ─── ACT ────────────────────────────────────────────────────────────────────
    duration = segment.duration_ms

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert duration == 15500.0


def test_media_segment_should_reject_start_greater_or_equal_to_end():
    """
    Given: Tiempos donde el inicio es mayor o igual al fin.
    When:  Se intenta instanciar MediaSegment.
    Then:  Levanta ValueError.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    start = 5000.0
    end_equal = 5000.0
    end_less = 4000.0

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    # Caso 1: Iguales
    with pytest.raises(ValueError) as exc_info_eq:
        MediaSegment(start_ms=start, end_ms=end_equal)
    msg_eq = str(exc_info_eq.value).lower()
    assert "start_ms" in msg_eq
    assert "end_ms" in msg_eq
    assert "menor" in msg_eq or "less" in msg_eq

    # Caso 2: Inicio mayor al fin
    with pytest.raises(ValueError) as exc_info_less:
        MediaSegment(start_ms=start, end_ms=end_less)
    msg_less = str(exc_info_less.value).lower()
    assert "start_ms" in msg_less
    assert "end_ms" in msg_less


def test_media_segment_should_reject_negative_timestamps():
    """
    Given: Un tiempo de inicio negativo.
    When:  Se intenta instanciar.
    Then:  Levanta ValueError (el tiempo de video no puede ser menor a 0).
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    invalid_start = -100.0
    valid_end = 5000.0

    # ─── ACT & ASSERT ───────────────────────────────────────────────────────────
    with pytest.raises(ValueError) as exc_info:
        MediaSegment(start_ms=invalid_start, end_ms=valid_end)

    msg = str(exc_info.value).lower()
    assert "start_ms" in msg
    assert "negativ" in msg


def test_media_segment_should_apply_padding_safely_without_going_below_zero():
    """
    Given: Un segmento que inicia cerca del 0 (ej: 0.5s) y un padding mayor (ej: 1.0s).
    When:  Se aplica el padding al segmento.
    Then:  El nuevo inicio se limita a 0.0s (no -0.5s), previniendo crashes en FFmpeg.
    Regla: DoD #3 Prueba de Padding.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    segment = MediaSegment(start_ms=500.0, end_ms=5000.0)
    pad = Padding(duration_ms=1000.0)

    # ─── ACT ────────────────────────────────────────────────────────────────────
    padded_segment = segment.apply_padding(pad)

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert padded_segment.start_ms == 0.0, (
        "El inicio no puede ser negativo, debe 'clipearse' a 0"
    )
    assert padded_segment.end_ms == 6000.0, (
        "El final debe extenderse sumando el padding"
    )
    # Inmutabilidad: el segmento original no debe alterarse
    assert segment.start_ms == 500.0


def test_media_segment_should_apply_padding_normally():
    """
    Given: Un segmento normal en el medio del video.
    When:  Se aplica el padding.
    Then:  Se resta del inicio y se suma al final.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    segment = MediaSegment(start_ms=10000.0, end_ms=20000.0)
    pad = Padding(duration_ms=1000.0)

    # ─── ACT ────────────────────────────────────────────────────────────────────
    padded_segment = segment.apply_padding(pad)

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    assert padded_segment.start_ms == 9000.0
    assert padded_segment.end_ms == 21000.0

