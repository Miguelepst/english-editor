# src/english_editor/modules/analysis/domain/exceptions.py
"""
Excepciones del dominio de Análisis.

Arquitectura: Domain Layer
Responsabilidad: Definir errores semánticos independientes de la infraestructura.
"""


class AnalysisError(Exception):
    """Clase base para errores en el módulo de análisis."""

    pass


class AudioFileError(AnalysisError):
    """El archivo de audio no existe, es ilegible o tiene formato inválido."""

    pass


class EngineRuntimeError(AnalysisError):
    """Fallo interno del motor de inferencia (ej: OOM, corrupción de modelo)."""

    pass


class MemoryLimitExceeded(EngineRuntimeError):
    """El proceso excedió el límite de memoria permitido (DR-03)."""

    pass
