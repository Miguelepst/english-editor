# tests/modules/analysis/infrastructure/test_observability.py
"""
Tests para: ObservabilityService (SRE Edition)
Tipo: Unitario
Validación Completa:
  1. Estructura de Logs (JSON)
  2. Manejo de Errores (Exceptions)
  3. Métricas SRE (Latency + RAM Saturation)
"""
import pytest
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import del SUT
from english_editor.modules.analysis.infrastructure.observability import ObservabilityService

class TestObservabilityService:

    # ─── 1. Pruebas de Utilidad Básica ────────────────────────────────────────

    def test_correlation_id_format(self):
        """Debe devolver un string de 8 caracteres."""
        cid = ObservabilityService.get_correlation_id()
        assert isinstance(cid, str)
        assert len(cid) == 8

    @patch("english_editor.modules.analysis.infrastructure.observability.logger")
    def test_log_structure_compliance(self, mock_logger):
        """Verifica que el JSON cumple el estándar para Datadog/ELK."""
        payload = {"user": "test"}
        ObservabilityService.log_event("test.evt", "123", payload)

        args, _ = mock_logger.info.call_args
        log_json = json.loads(args[0])

        required = ["timestamp", "level", "event", "correlation_id", "data"]
        for field in required:
            assert field in log_json

    # ─── 2. Pruebas de Decorador & Métricas SRE (RAM) ─────────────────────────

    @patch("english_editor.modules.analysis.infrastructure.observability.psutil")
    @patch("english_editor.modules.analysis.infrastructure.observability.logger")
    def test_measure_latency_should_log_ram_metrics(self, mock_logger, mock_psutil):
        """
        Happy Path SRE:
        Verifica que al ejecutar exitosamente, se registran métricas de RAM.
        """
        # Arrange: Simulamos consumo de RAM (100 MB)
        process_mock = MagicMock()
        process_mock.memory_info.return_value.rss = 104857600 # 100 MB en bytes
        mock_psutil.Process.return_value = process_mock

        @ObservabilityService.measure_latency("sre_op")
        def work():
            return "done"

        # Act
        work()

        # Assert
        # Verificamos la llamada de "completed"
        last_call = mock_logger.info.call_args_list[-1]
        log_json = json.loads(last_call[0][0])

        data = log_json["data"]
        # Validar campos SRE
        assert "duration_sec" in data
        assert "end_ram_mb" in data
        assert "ram_delta_mb" in data
        assert data["end_ram_mb"] == 100.0
        assert data["status"] == "success"

    # ─── 3. Pruebas de Manejo de Errores ──────────────────────────────────────

    @patch("english_editor.modules.analysis.infrastructure.observability.psutil")
    @patch("english_editor.modules.analysis.infrastructure.observability.logger")
    def test_measure_latency_should_reraise_and_log_crash_ram(self, mock_logger, mock_psutil):
        """
        Error Path SRE:
        Si falla, debe loguear cuánta RAM había al momento del crash y re-lanzar error.
        """
        # Arrange: ¡AQUÍ ESTABA EL ERROR!
        # Debemos configurar el mock igual que arriba para que devuelva un float.
        process_mock = MagicMock()
        process_mock.memory_info.return_value.rss = 52428800 # 50 MB en bytes
        mock_psutil.Process.return_value = process_mock

        @ObservabilityService.measure_latency("fail_op")
        def broken():
            raise ValueError("Critical Failure")

        # Act & Assert
        with pytest.raises(ValueError):
            broken()

        # Verificar log de error
        mock_logger.error.assert_called_once()
        error_call = mock_logger.error.call_args
        log_json = json.loads(error_call[0][0])

        assert log_json["event"] == "fail_op.failed"
        assert log_json["data"]["error_msg"] == "Critical Failure"

        # Verificar que capturó la RAM del crash (que ahora es un float 50.0, no un Mock)
        assert "crash_ram_mb" in log_json["data"]
        assert log_json["data"]["crash_ram_mb"] == 50.0

    # ─── 4. Prueba de Contexto (Archivos) ─────────────────────────────────────

    @patch("english_editor.modules.analysis.infrastructure.observability.logger")
    def test_context_extraction(self, mock_logger):
        """Si se pasa un Path, debe salir en los logs."""
        @ObservabilityService.measure_latency("file_op")
        def read_file(f): pass

        read_file(Path("video.mp4"))

        last_call = mock_logger.info.call_args_list[-1]
        log_json = json.loads(last_call[0][0])
        assert log_json["data"]["target"] == "video.mp4"