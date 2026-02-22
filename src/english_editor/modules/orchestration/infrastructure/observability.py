# src/english_editor/modules/orchestration/infrastructure/observability.py
"""
Configuración centralizada de Logging y Métricas.

Principios SRE:
1. Logs estructurados para máquinas (Archivo).
2. Logs legibles para humanos (Consola).
3. Contexto (Job ID) en cada línea.
"""

import logging
import sys
import time
from functools import wraps
from typing import Any, Callable

# Configuración Global
LOG_FILE = "system_execution.log"


def configure_logging(level=logging.INFO):
    """
    Configura el sistema de logging con doble destino (File + Console).
    """
    # Formateador simple para consola
    console_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s", datefmt="%H:%M:%S"
    )

    # Formateador detallado para archivo (Forensics)
    file_formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
    )

    # Handler Consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(level)

    # Handler Archivo
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)  # Siempre capturamos todo en disco

    # Root Logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capturar todo desde la raíz

    # Limpiar handlers previos para evitar duplicados en Colab
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.info(f"🔭 Observabilidad iniciada. Logs persistentes en: {LOG_FILE}")


# === Decoradores de Métricas (Instrumentation) ===


def measure_time(metric_name: str):
    """
    Decorador para medir latencia de funciones críticas.
    Principio: 'Measure what matters' - Performance.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.perf_counter() - start_time
                # Logueamos como métrica estructurada
                logging.getLogger("metrics").info(
                    f"[METRIC] {metric_name} duration={duration:.4f}s"
                )

        return wrapper

    return decorator
