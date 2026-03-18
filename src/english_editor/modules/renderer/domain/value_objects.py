# src/english_editor/modules/renderer/domain/value_objects.py
"""
Value Objects para el renderizado y empalme de medios (FFmpeg Domain).

Arquitectura: Modular Monolith + Vertical Slice
Componente: Domain / Value Objects
Responsabilidad: Encapsular y validar las reglas matemáticas inmutables del tiempo de los medios (cortes, padding, sincronización) sin depender de librerías externas.
"""
from __future__ import annotations
from dataclasses import dataclass

# === 🧭 Protocolos Arquitectónicos (Strict Layering) ===
# ✅ CORE: Building blocks universales (value objects, tipos básicos)
# ✅ MODULES: Bounded contexts verticales y aislados
# ❌ DOMAIN → APPLICATION/INFRA: Prohibido (rompe Clean Architecture)
# ❌ MODULES → MODULES: Prohibido (comunicación solo vía Core o Puertos)
# ✅ INFRASTRUCTURE: Solo adaptadores concretos (nunca lógica de negocio)

# === 🧪 Protocolos de Calidad Obligatorios ===
# 🔒 Inmutabilidad: Value Objects → @dataclass(frozen=True)
# 🧪 Testabilidad: Componente debe ser testeable SIN mocks de infraestructura
# 🔤 Type Hints: Firmas públicas con type hints explícitos (PEP 484)
# ⚡ Pureza: Funciones puras donde sea posible (misma entrada → misma salida)
# 🚫 Excepciones específicas: Define excepciones de dominio (no uses Exception genérico)
# 📏 Longitud de línea: Máximo 88 caracteres (compatible con Black/Ruff)


# === Definición principal ===

@dataclass(frozen=True)
class Padding:
    """
    Define el margen de seguridad de tiempo para inyectar a un corte de audio/video.
    Garantiza que el tiempo inyectado nunca sea destructivo (negativo).
    """
    duration_ms: float

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError(
                f"La duración del padding (duration_ms) no puede ser un valor negativo: {self.duration_ms}"
            )


@dataclass(frozen=True)
class MediaSegment:
    """
    Representa un bloque de tiempo continuo de un archivo multimedia.
    Asegura la coherencia matemática del intervalo de tiempo.
    """
    start_ms: float
    end_ms: float

    def __post_init__(self) -> None:
        if self.start_ms < 0:
            raise ValueError(
                f"El inicio del segmento (start_ms) no puede ser negativo: {self.start_ms}"
            )
        if self.start_ms >= self.end_ms:
            raise ValueError(
                f"El inicio del segmento start_ms ({self.start_ms}) debe ser estrictamente menor que el final end_ms ({self.end_ms})."
            )

    @property
    def duration_ms(self) -> float:
        """Calcula la duración exacta del segmento."""
        return self.end_ms - self.start_ms

    def apply_padding(self, padding: Padding) -> MediaSegment:
        """
        Aplica un margen de seguridad (padding) al segmento.
        Retorna un nuevo MediaSegment inmutable.
        Previene el colapso garantizando que el nuevo inicio no baje de 0.0ms.
        """
        # Regla de Negocio DoD #3: Clipear el inicio a 0 si el padding lo empuja hacia valores negativos.
        new_start = max(0.0, self.start_ms - padding.duration_ms)
        new_end = self.end_ms + padding.duration_ms
        
        return MediaSegment(start_ms=new_start, end_ms=new_end)


# === Protección contra ejecución directa ===
if __name__ == "__main__":
    # ⚠️ Evita lógica de negocio aquí. Usa tests/ para validación.
    # ✅ Solo para demos controladas o scripts utilitarios.
    pass
