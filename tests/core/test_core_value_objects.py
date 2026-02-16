import pytest

from english_editor.core.value_objects import PositiveValue


def test_positive_value_accepts_valid():
    assert PositiveValue(5).value == 5


def test_positive_value_rejects_zero():
    with pytest.raises(ValueError, match="Must be positive"):
        PositiveValue(0)
