
# @title 🧪 test_dast_cli.py — [DAST] CLI Security Fuzzing

# ✅ Test DAST creado en tu nueva rama: /content/english-editor/tests/security/test_dast_cli.py

# tests/security/test_dast_cli.py
"""
Dynamic Application Security Testing (DAST) / Fuzzer para la CLI.

Tipo: Integración/Seguridad (Caja Negra)
Objetivo: Validar que la CLI maneja inputs maliciosos de forma segura (Fail Gracefully),
          sin exponer Stack Traces ni permitir acceso no autorizado al File System.
"""

import subprocess
import sys
from pathlib import Path

import pytest

# === Variables de Entorno para el Ataque ===
CLI_MODULE = "english_editor.modules.analysis.presentation.cli"


def run_cli_attack(target_input: str) -> subprocess.CompletedProcess:
    """Ejecuta la CLI en un subproceso simulando a un atacante real en la terminal."""
    # Usamos sys.executable para garantizar que usamos el mismo entorno Python
    cmd = [sys.executable, "-m", CLI_MODULE, str(target_input)]

    # Capturamos stdout y stderr para analizar la respuesta
    return subprocess.run(cmd, capture_output=True, text=True)


# === Escenarios de Ataque DAST ===


@pytest.mark.security
def test_dast_path_traversal_attack():
    """
    Given: Un atacante intentando leer archivos del sistema (LFI / Path Traversal).
    When:  Se inyecta una ruta crítica del SO operativo como input.
    Then:  La aplicación bloquea el acceso, no crashea con Stack Trace,
           y devuelve un código de error de aplicación (sys.exit(1)).
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    # Vector de ataque clásico en Linux
    malicious_input = "../../../../etc/passwd"

    # ─── ACT ────────────────────────────────────────────────────────────────────
    result = run_cli_attack(malicious_input)

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    # 1. Verificar código de salida (1 = Error controlado de validación en cli.py)
    assert result.returncode == 1, (
        "La CLI no devolvió el código de error esperado para archivo no encontrado."
    )

    # 2. Verificar fuga de información (No Stack Trace)
    assert "Traceback" not in result.stderr, (
        "VULNERABILIDAD: La CLI filtró un Stack Trace al atacante."
    )

    # 3. Verificar que no se leyó el contenido (ej: root:x:0:0)
    assert "root:x" not in result.stdout
    assert "root:x" not in result.stderr

    # 4. Verificar mensaje de usuario seguro
    # assert "no existe" in result.stderr.lower()

    # 4. Verificar mensaje de usuario seguro (Puede ser por no existir o por extensión inválida)
    assert any(
        msg in result.stderr.lower()
        for msg in ["no existe", "no permitida", "seguridad"]
    )


@pytest.mark.security
def test_dast_poisoned_file_attack(tmp_path):
    """
    Given: Un atacante subiendo un archivo corrupto o envenenado (texto haciéndose pasar por audio).
    When:  El motor intenta procesarlo y falla internamente (Librosa/Whisper).
    Then:  La CLI atrapa el error profundo, lo empaqueta en un AnalysisError,
           y sale limpiamente sin mostrar la arquitectura interna (sys.exit(2)).
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    poisoned_file = tmp_path / "fake_audio.wav"
    # Escribimos un payload malicioso o texto plano en lugar de bytes de audio reales
    poisoned_file.write_text("<?php system($_GET['cmd']); ?> Esto no es un audio.")

    # ─── ACT ────────────────────────────────────────────────────────────────────
    result = run_cli_attack(str(poisoned_file))

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    # 1. Falla controlada de dominio (Código 2 según definimos en cli.py para AnalysisError)
    assert result.returncode == 2, (
        f"Se esperaba código 2, se obtuvo: {result.returncode}"
    )

    # 2. Prevención de fuga de información interna
    assert "Traceback" not in result.stderr, (
        "VULNERABILIDAD: La CLI filtró un Stack Trace profundo."
    )

    # 3. Respuesta estándar al usuario
    assert "error de análisis" in result.stderr.lower()


@pytest.mark.security
def test_dast_empty_file_denial_of_service(tmp_path):
    """
    Given: Un atacante enviando un archivo de 0 bytes (potencial DoS o división por cero).
    When:  Se inyecta en la CLI.
    Then:  La aplicación no entra en loop infinito ni crashea violentamente.
    """
    # ─── ARRANGE ────────────────────────────────────────────────────────────────
    empty_file = tmp_path / "zero_bytes.wav"
    empty_file.touch()  # Archivo vacío

    # ─── ACT ────────────────────────────────────────────────────────────────────
    result = run_cli_attack(str(empty_file))

    # ─── ASSERT ─────────────────────────────────────────────────────────────────
    # Aseguramos que el programa termina y no se queda colgado, fallando con gracia.
    assert result.returncode != 0, "Debería fallar al procesar un audio vacío."
    assert "Traceback" not in result.stderr, (
        "VULNERABILIDAD: Filtrado de Stack Trace en DoS."
    )

