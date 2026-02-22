"""Módulo de observabilidad para métricas y logging del sistema."""

# Importe opcional con fallback para CI/CD
try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    _PSUTIL_AVAILABLE = False

try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    _PSUTIL_AVAILABLE = False

"""
Servicio de Observabilidad SRE: Logs, Latency & Saturation (RAM).
Soporta modo "Pretty Print" para depuración visual.
"""

import functools
import json
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Callable

import psutil

# Configuración básica
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("english_editor")


class ObservabilityService:

    # 🌍 CONFIGURACIÓN GLOBAL
    # Si esta variable de entorno existe, activamos la vista vertical
    PRETTY_PRINT = os.getenv("LOG_FORMAT") == "PRETTY"

    @staticmethod
    def get_correlation_id() -> str:
        return str(uuid.uuid4())[:8]

    @staticmethod
    def _get_ram_usage_mb() -> float:
        try:
            process = psutil.Process(os.getpid())
            return round(process.memory_info().rss / 1024 / 1024, 2)
        except Exception:
            return 0.0

    @staticmethod
    def log_event(
        event_name: str,
        correlation_id: str,
        payload: dict[str, Any],
        level: str = "INFO",
    ):
        """Emite un log estructurado en JSON (Horizontal o Vertical)."""

        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "event": event_name,
            "correlation_id": correlation_id,
            "data": payload,
        }

        # 🎨 LÓGICA DE VISUALIZACIÓN
        if ObservabilityService.PRETTY_PRINT:
            # MODO VERTICAL (Human-Readable)
            # Usamos indent=4 para que se vea bonito hacia abajo
            msg = json.dumps(log_entry, indent=4)
        else:
            # MODO HORIZONTAL (Machine-Readable - Default)
            msg = json.dumps(log_entry)

        if level == "ERROR":
            logger.error(msg)
        else:
            logger.info(msg)

    @staticmethod
    def measure_latency(operation_name: str):
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_ram = ObservabilityService._get_ram_usage_mb()
                correlation_id = ObservabilityService.get_correlation_id()

                file_context = "unknown"
                for arg in args:
                    if isinstance(arg, Path):
                        file_context = arg.name
                        break

                ObservabilityService.log_event(
                    event_name=f"{operation_name}.started",
                    correlation_id=correlation_id,
                    payload={"target": file_context, "start_ram_mb": start_ram},
                )

                try:
                    result = func(*args, **kwargs)

                    end_time = time.time()
                    end_ram = ObservabilityService._get_ram_usage_mb()

                    ObservabilityService.log_event(
                        event_name=f"{operation_name}.completed",
                        correlation_id=correlation_id,
                        payload={
                            "duration_sec": round(end_time - start_time, 3),
                            "end_ram_mb": end_ram,
                            "ram_delta_mb": round(end_ram - start_ram, 2),
                            "target": file_context,
                            "status": "success",
                        },
                    )
                    return result

                except Exception as e:
                    end_time = time.time()
                    crash_ram = ObservabilityService._get_ram_usage_mb()

                    ObservabilityService.log_event(
                        event_name=f"{operation_name}.failed",
                        correlation_id=correlation_id,
                        payload={
                            "duration_sec": round(end_time - start_time, 3),
                            "crash_ram_mb": crash_ram,
                            "target": file_context,
                            "error_type": type(e).__name__,
                            "error_msg": str(e),
                        },
                        level="ERROR",
                    )
                    raise e

            return wrapper

        return decorator
