# tests/modules/analysis/domain/test_value_objects.py
"""
Tests para: TimeRange
Tipo: Unitario (Domain)
"""
import pytest
from english_editor.modules.analysis.domain.value_objects import TimeRange

# === Casos de Prueba ===

def test_timerange_creation_valid():
    """
    Given: Un inicio y fin válidos
    When: Se instancia TimeRange
    Then: El objeto se crea correctamente
    """
    # Arrange & Act
    tr = TimeRange(start=10.0, end=20.5)

    # Assert
    assert tr.start == 10.0
    assert tr.end == 20.5
    assert tr.duration == 10.5

def test_timerange_rejects_negative_start():
    """
    Given: Un inicio negativo
    When: Se instancia TimeRange
    Then: Lanza ValueError
    """
    # Arrange, Act & Assert
    with pytest.raises(ValueError) as exc_info:
        TimeRange(start=-1.0, end=10.0)

    assert "negativo" in str(exc_info.value).lower()

def test_timerange_rejects_end_before_start():
    """
    Given: Un fin menor que el inicio
    When: Se instancia TimeRange
    Then: Lanza ValueError (Invariante DR-01)
    """
    # Arrange, Act & Assert
    with pytest.raises(ValueError) as exc_info:
        TimeRange(start=10.0, end=9.0)

    assert "menor al inicio" in str(exc_info.value).lower()

def test_timerange_overlaps_logic():
    """
    Given: Dos rangos que se cruzan
    When: Se llama a overlaps_with
    Then: Devuelve True
    """
    # Arrange
    r1 = TimeRange(0, 10)
    r2 = TimeRange(5, 15)   # Solapa
    r3 = TimeRange(10, 20)  # Toca (no solapa estrictamente para intersección)
    r4 = TimeRange(11, 20)  # Disjunto

    # Act & Assert
    assert r1.overlaps_with(r2) is True
    assert r1.overlaps_with(r4) is False
    # Nota: Dependiendo de la definición matemática, tocar el borde puede no ser overlap.
    # En esta impl: max(0,10) < min(10,20) -> 10 < 10 -> False. Correcto.

def test_timerange_merge_logic():
    """
    Given: Dos rangos solapados
    When: Se fusionan
    Then: Resulta en un rango extendido
    """
    # Arrange
    r1 = TimeRange(0, 10)
    r2 = TimeRange(5, 15)

    # Act
    merged = r1.merge(r2)

    # Assert
    assert merged == TimeRange(0, 15)

def test_timerange_merge_disjoint_raises_error():
    """
    Given: Dos rangos separados
    When: Se intenta fusionar
    Then: Lanza ValueError
    """
    # Arrange
    r1 = TimeRange(0, 10)
    r2 = TimeRange(12, 20)

    # Act & Assert
    with pytest.raises(ValueError) as exc_info:
        r1.merge(r2)

    assert "disjuntos" in str(exc_info.value).lower()