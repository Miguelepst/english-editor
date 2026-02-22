# src/english_editor/modules/analysis/domain/value_objects.py
"""
TimeRange Value Object.

Arquitectura: Modular Monolith
Componente: Value Object (Domain)
Responsabilidad: Representar un intervalo de tiempo validado e inmutable.
"""

from __future__ import annotations

from dataclasses import dataclass

# === 🧭 Protocolos Arquitectónicos ===
# ✅ CORE: No depende de nada externo.
# 🔒 Inmutabilidad: frozen=True.


@dataclass(frozen=True)
class TimeRange:
    """
    Representa un intervalo de tiempo contiguo en segundos.

    Invariantes:
    1. start >= 0
    2. end >= start
    """

    start: float
    end: float

    def __post_init__(self):
        """Validación de invariantes al instanciar."""
        if self.start < 0:
            raise ValueError(f"El inicio no puede ser negativo: {self.start}")
        if self.end < self.start:
            raise ValueError(
                f"El fin ({self.end}) no puede ser menor al inicio ({self.start})"
            )

    @property
    def duration(self) -> float:
        """Calcula la duración del intervalo."""
        return round(self.end - self.start, 3)

    def overlaps_with(self, other: TimeRange) -> bool:
        """Determina si este rango se solapa con otro."""
        return max(self.start, other.start) < min(self.end, other.end)

    def merge(self, other: TimeRange) -> TimeRange:
        """
        Combina dos rangos solapados o contiguos en uno solo.
        Lanza ValueError si los rangos son disjuntos.
        """
        # Se permite merge si se solapan o si se tocan (son contiguos)
        # La condición de "tocarse" es self.end == other.start o viceversa.
        if (
            not self.overlaps_with(other)
            and self.end != other.start
            and self.start != other.end
        ):
            raise ValueError(
                f"No se pueden fusionar rangos disjuntos: {self} y {other}"
            )

        return TimeRange(
            start=min(self.start, other.start), end=max(self.end, other.end)
        )
