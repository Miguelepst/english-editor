# src/english_editor/infrastructure/devsecops/devsecops_orchestrator.py
"""
Plataforma extensible para orquestación DevSecOps (Secrets, SAST, SCA, Image Scan, Licenses).

Arquitectura: Modular Monolith + Vertical Slice
Componente: Infrastructure / CI-CD
Responsabilidad: Orquestar la ejecución de pruebas de seguridad integradas en el pipeline de CI/CD.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
from dataclasses import asdict, dataclass, field

# 🔴 ANTES:
# from datetime import datetime
# 🟢 DESPUÉS:
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

# rich para visualización profesional en terminal
try:
    from rich import box  # 🟢 AGREGAR ESTA LÍNEA AQUÍ 🟢
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

    def Console(**kw):
        return type("MockConsole", (), {"print": print, "rule": lambda *a, **k: None})()


# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN DE LOGGING
# ─────────────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)-8s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# ENUMS Y TIPOS BASE
# ─────────────────────────────────────────────────────────────────────────────
class TestSeverity(Enum):
    """Niveles de severidad para hallazgos de seguridad"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
    UNKNOWN = "unknown"


class TestStatus(Enum):
    """Estados posibles de una prueba de seguridad"""

    PASSED = auto()
    FAILED = auto()
    WARNING = auto()
    SKIPPED = auto()
    ERROR = auto()


@dataclass(frozen=True)
class SecurityFinding:
    """Representa un hallazgo individual de seguridad"""

    id: str
    title: str
    severity: TestSeverity
    description: str
    location: str | None = None
    cve: str | None = None
    fix_recommendation: str | None = None
    raw_data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            **asdict(self),
            "severity": self.severity.value,
        }


@dataclass
class TestResult:
    """Resultado de una prueba de seguridad ejecutada"""

    test_name: str
    status: TestStatus
    findings: list[SecurityFinding] = field(default_factory=list)
    execution_time_seconds: float = 0.0
    output_log: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_critical_issues(self) -> bool:
        return any(f.severity == TestSeverity.CRITICAL for f in self.findings)

    @property
    def has_high_issues(self) -> bool:
        return any(f.severity == TestSeverity.HIGH for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_name": self.test_name,
            "status": self.status.name,
            "findings": [f.to_dict() for f in self.findings],
            "execution_time_seconds": self.execution_time_seconds,
            "metadata": self.metadata,
            "summary": {
                "total_findings": len(self.findings),
                "critical": sum(
                    1 for f in self.findings if f.severity == TestSeverity.CRITICAL
                ),
                "high": sum(
                    1 for f in self.findings if f.severity == TestSeverity.HIGH
                ),
                "medium": sum(
                    1 for f in self.findings if f.severity == TestSeverity.MEDIUM
                ),
            },
        }


# ─────────────────────────────────────────────────────────────────────────────
# PROTOCOLOS (Contratos para Plugins - DIP)
# ─────────────────────────────────────────────────────────────────────────────
@runtime_checkable
class SecurityTestPlugin(Protocol):
    """
    Contrato que debe cumplir cualquier plugin de prueba de seguridad.
    Permite extender el sistema sin modificar el orchestrator (OCP).
    """

    name: str
    description: str

    def is_applicable(self, project_path: Path) -> bool:
        """¿Esta prueba aplica para este proyecto? (por defecto: siempre)"""
        return True

    def execute(self, project_path: Path, **kwargs) -> TestResult:
        """Ejecuta la prueba y retorna resultados estructurados"""
        ...


# ─────────────────────────────────────────────────────────────────────────────
# REPORT ENGINE: Visualización y Exportación
# ─────────────────────────────────────────────────────────────────────────────
class ReportEngine:
    """Genera reportes en múltiples formatos con visualización profesional"""

    def __init__(self, use_rich: bool = True):
        self.console = Console() if use_rich and RICH_AVAILABLE else None
        self.use_rich = use_rich and RICH_AVAILABLE

    def print_header(self, title: str, subtitle: str = "") -> None:
        """Imprime encabezado estilizado"""
        if self.use_rich:
            self.console.rule(f"[bold cyan]{title}[/]", align="center")
            if subtitle:
                self.console.print(f"[dim]{subtitle}[/]", justify="center")
        else:
            print(f"\n{'='*60}\n{title}\n{'='*60}")
            if subtitle:
                print(subtitle)

    def print_test_result(self, result: TestResult) -> None:
        """Visualiza el resultado de una prueba individual"""
        status_icons = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.WARNING: "⚠️",
            TestStatus.SKIPPED: "⤷",
            TestStatus.ERROR: "💥",
        }
        status_colors = {
            TestStatus.PASSED: "green",
            TestStatus.FAILED: "red",
            TestStatus.WARNING: "yellow",
            TestStatus.SKIPPED: "dim",
            TestStatus.ERROR: "magenta",
        }

        icon = status_icons.get(result.status, "❓")
        color = status_colors.get(result.status, "white")

        if self.use_rich:
            self.console.print(
                f"[{color}]{icon} {result.test_name}[/]: "
                f"[bold {color}]{result.status.name}[/] "
                f"({result.execution_time_seconds:.1f}s)"
            )

            if result.findings:
                table = Table(show_header=True, header_style="bold", box=None)
                table.add_column("Severidad", style="dim")
                table.add_column("ID")
                table.add_column("Título")
                table.add_column("Ubicación", style="dim")

                severity_styles = {
                    TestSeverity.CRITICAL: "bold red",
                    TestSeverity.HIGH: "red",
                    TestSeverity.MEDIUM: "yellow",
                    TestSeverity.LOW: "blue",
                    TestSeverity.INFO: "dim",
                }

                for finding in result.findings:
                    style = severity_styles.get(finding.severity, "white")
                    table.add_row(
                        f"[{style}]{finding.severity.value.upper()}[/{style}]",
                        finding.id,
                        finding.title,
                        finding.location or "N/A",
                    )
                self.console.print(table)
        else:
            print(
                f"{icon} {result.test_name}: {result.status.name} ({result.execution_time_seconds:.1f}s)"
            )
            for f in result.findings:
                print(f"   • [{f.severity.value.upper()}] {f.id}: {f.title}")

    def print_summary(self, results: list[TestResult]) -> None:
        """Imprime resumen ejecutivo de todas las pruebas"""
        total = len(results)
        passed = sum(1 for r in results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results if r.status == TestStatus.FAILED)
        warnings = sum(1 for r in results if r.status == TestStatus.WARNING)

        total_findings = sum(len(r.findings) for r in results)
        critical = sum(
            sum(1 for f in r.findings if f.severity == TestSeverity.CRITICAL)
            for r in results
        )
        high = sum(
            sum(1 for f in r.findings if f.severity == TestSeverity.HIGH)
            for r in results
        )

        if self.use_rich:
            # 🔴 CAMBIAR ESTO:
            # summary_table = Table(title="📊 Resumen Ejecutivo de Seguridad", box="ROUNDED")
            # 🟢 POR ESTO:
            summary_table = Table(
                title="📊 Resumen Ejecutivo de Seguridad", box=box.ROUNDED
            )
            summary_table.add_column("Métrica", style="cyan")
            summary_table.add_column("Valor", justify="right")

            summary_table.add_row("Pruebas ejecutadas", str(total))
            summary_table.add_row("✅ Aprobadas", f"[green]{passed}[/]")
            summary_table.add_row(
                "❌ Fallidas", f"[red]{failed}[/]" if failed else str(failed)
            )
            summary_table.add_row("⚠️ Con advertencias", str(warnings))
            summary_table.add_row("", "")  # Separador
            summary_table.add_row("Hallazgos totales", str(total_findings))
            summary_table.add_row(
                "🔴 Críticos", f"[bold red]{critical}[/]" if critical else "0"
            )
            summary_table.add_row("🟠 Altos", f"[red]{high}[/]" if high else "0")

            self.console.print(summary_table)

            # Panel de recomendación
            if critical > 0:
                recommendation = "[bold red]🚨 ACCIÓN INMEDIATA REQUERIDA[/]: Corregir vulnerabilidades críticas antes de continuar."
            elif high > 0:
                recommendation = "[bold yellow]⚠️ REVISIÓN RECOMENDADA[/]: Atender vulnerabilidades altas en el próximo sprint."
            elif failed > 0:
                recommendation = "[bold blue]ℹ️  MEJORA CONTINUA[/]: Revisar pruebas fallidas para fortalecer la postura de seguridad."
            else:
                recommendation = "[bold green]✅ POSTURA DE SEGURIDAD SÓLIDA[/]: Continuar con el desarrollo. Programar próximo escaneo."

            self.console.print(
                Panel(recommendation, title="🎯 Recomendación", border_style="green")
            )
        else:
            print(
                f"\n📊 Resumen: {passed}/{total} aprobadas, {critical} críticos, {high} altos"
            )

    def export_json(self, results: list[TestResult], output_path: Path) -> Path:
        """Exporta resultados a JSON estructurado"""
        report = {
            #'generated_at': datetime.utcnow().isoformat() + 'Z',      # 🔴 ANTES:
            "generated_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),  # 🟢 DESPUÉS
            "orchestrator_version": "1.0.0",
            "summary": {
                "total_tests": len(results),
                "passed": sum(1 for r in results if r.status == TestStatus.PASSED),
                "failed": sum(1 for r in results if r.status == TestStatus.FAILED),
                "total_findings": sum(len(r.findings) for r in results),
            },
            "results": [r.to_dict() for r in results],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, indent=2, default=str))
        logger.info(f"📄 Reporte JSON exportado: {output_path}")
        return output_path

    def export_html(self, results: list[TestResult], output_path: Path) -> Path:
        """Exporta resultados a HTML interactivo (básico, extensible)"""
        # Plantilla HTML con Tema Oscuro (Dark Mode)
        html_template = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Reporte de Seguridad</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.6; background-color: #121212; color: #e0e0e0; }}
  h1, h2, h3 {{ color: #ffffff; }}
  .header {{ text-align: center; border-bottom: 2px solid #333; padding-bottom: 1rem; }}
  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin: 2rem 0; }}
  .metric {{ background: #1e1e1e; padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid #2d2d2d; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
  .metric p {{ color: #aaaaaa; margin-top: 0.5rem; }}
  .metric.critical {{ background: rgba(244, 67, 54, 0.1); border-color: rgba(244, 67, 54, 0.3); border-left: 4px solid #f44336; }}
  .finding {{ margin: 1rem 0; padding: 1rem; border-left: 4px solid #2196f3; background: #1e1e1e; border-radius: 0 8px 8px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
  .finding.critical {{ border-color: #f44336; background: rgba(244, 67, 54, 0.05); }}
  .finding.high {{ border-color: #ff9800; background: rgba(255, 152, 0, 0.05); }}
  .finding.medium {{ border-color: #ffeb3b; background: rgba(255, 235, 59, 0.05); }}
  .finding strong {{ color: #ffffff; }}
  small {{ color: #999999; display: block; margin-top: 0.25rem; }}
  table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
  th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #333; }}
  th {{ background: #2d2d2d; color: #ffffff; }}
</style></head><body>
<div class="header"><h1>🛡️ Reporte de Seguridad DevSecOps</h1><p style="color: #888;">Generado: {generated_at}</p></div>
<div class="summary">
  <div class="metric"><h3 style="margin:0; font-size: 2rem;">{total_tests}</h3><p style="margin:0;">Pruebas</p></div>
  <div class="metric"><h3 style="margin:0; font-size: 2rem; color: #4caf50;">{passed}</h3><p style="margin:0;">Aprobadas</p></div>
  <div class="metric critical"><h3 style="margin:0; font-size: 2rem; color: #f44336;">{critical}</h3><p style="margin:0;">Críticos</p></div>
  <div class="metric"><h3 style="margin:0; font-size: 2rem; color: #ff9800;">{high}</h3><p style="margin:0;">Altos</p></div>
</div>
{results_html}
</body></html>"""

        results_html = ""
        for r in results:
            if r.findings:
                findings_html = "\n".join(
                    f'<div class="finding {f.severity.value}">'
                    f"<strong>[{f.severity.value.upper()}] {f.id}</strong>: {f.title}"
                    f'{"<br><small>Ubicación: " + f.location + "</small>" if f.location else ""}'
                    f'{"<br><small>CVE: " + f.cve + "</small>" if f.cve else ""}'
                    f"</div>"
                    for f in r.findings
                )
                results_html += f"<h3>{r.test_name}</h3>{findings_html}"

        summary = {
            #'generated_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),          # 🔴 ANTES
            "generated_at": datetime.now(timezone.utc).strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            ),  # 🟢 DESPUÉS
            "total_tests": len(results),
            "passed": sum(1 for r in results if r.status == TestStatus.PASSED),
            "critical": sum(
                sum(1 for f in r.findings if f.severity == TestSeverity.CRITICAL)
                for r in results
            ),
            "high": sum(
                sum(1 for f in r.findings if f.severity == TestSeverity.HIGH)
                for r in results
            ),
            "results_html": results_html,
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_template.format(**summary))
        logger.info(f"🌐 Reporte HTML exportado: {output_path}")
        return output_path


# ─────────────────────────────────────────────────────────────────────────────
# PLUGINS CONCRETOS DE PRUEBAS (Ejemplos extensibles)
# ─────────────────────────────────────────────────────────────────────────────
class SecretsTest:
    """Plugin: Detección de secretos expuestos (Gitleaks)"""

    name = "secrets"
    description = (
        "Escanea código en busca de API keys, tokens y credenciales hardcodeadas"
    )

    def is_applicable(self, project_path: Path) -> bool:
        return (project_path / ".git").exists() or any(project_path.glob("*.py"))

    def execute(self, project_path: Path, **kwargs) -> TestResult:
        import time

        start = time.time()
        findings = []

        try:
            cmd = [
                "gitleaks",
                "detect",
                "--source",
                str(project_path),
                "--no-git",
                "-v",
                "--report-format",
                "json",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, cwd=project_path
            )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    leaks = json.loads(result.stdout)
                    for leak in leaks if isinstance(leaks, list) else []:
                        findings.append(
                            SecurityFinding(
                                id=leak.get("RuleID", "UNKNOWN"),
                                title=leak.get("Description", "Secreto detectado"),
                                severity=TestSeverity.HIGH,
                                description=f"Secreto potencial en {leak.get('File', 'unknown')}",
                                location=f"{leak.get('File')}:{leak.get('StartLine', '?')}",
                                fix_recommendation="Eliminar credenciales del código y usar variables de entorno",
                                raw_data=leak,
                            )
                        )
                except json.JSONDecodeError:
                    pass

            status = TestStatus.FAILED if findings else TestStatus.PASSED

        except FileNotFoundError:
            return TestResult(
                test_name=self.name,
                status=TestStatus.SKIPPED,
                output_log="gitleaks no encontrado en PATH",
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return TestResult(
                test_name=self.name,
                status=TestStatus.ERROR,
                output_log=str(e),
                execution_time_seconds=time.time() - start,
            )

        return TestResult(
            test_name=self.name,
            status=status,
            findings=findings,
            execution_time_seconds=time.time() - start,
            output_log=result.stdout + result.stderr,
            metadata={"tool": "gitleaks", "version": "8.18.2"},
        )


class SASTTest:
    """Plugin: Análisis estático de código Python (Bandit)"""

    name = "sast"
    description = (
        "Detecta vulnerabilidades comunes en código Python (eval, SQL injection, etc.)"
    )

    def is_applicable(self, project_path: Path) -> bool:
        return any(project_path.rglob("*.py"))

    def execute(self, project_path: Path, **kwargs) -> TestResult:
        import time

        start = time.time()
        findings = []

        try:
            src_dir = (
                project_path / "src"
                if (project_path / "src").exists()
                else project_path
            )
            cmd = ["python", "-m", "bandit", "-r", str(src_dir), "-f", "json", "-ll"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300, cwd=project_path
            )

            if result.returncode != 0 or result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    for issue in data.get("results", []):
                        severity_map = {
                            "HIGH": TestSeverity.HIGH,
                            "MEDIUM": TestSeverity.MEDIUM,
                            "LOW": TestSeverity.LOW,
                        }
                        findings.append(
                            SecurityFinding(
                                id=issue.get("test_id", "B000"),
                                title=issue.get("test_name", "Issue de seguridad"),
                                severity=severity_map.get(
                                    issue.get("issue_severity", "LOW"),
                                    TestSeverity.INFO,
                                ),
                                description=issue.get("issue_text", ""),
                                location=f"{issue.get('filename')}:{issue.get('line_number')}",
                                fix_recommendation=issue.get("more_info", ""),
                                raw_data=issue,
                            )
                        )
                except json.JSONDecodeError:
                    pass

            has_high = any(
                f.severity in [TestSeverity.HIGH, TestSeverity.CRITICAL]
                for f in findings
            )
            status = (
                TestStatus.FAILED
                if has_high
                else (TestStatus.WARNING if findings else TestStatus.PASSED)
            )

        except FileNotFoundError:
            return TestResult(
                test_name=self.name,
                status=TestStatus.SKIPPED,
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return TestResult(
                test_name=self.name,
                status=TestStatus.ERROR,
                output_log=str(e),
                execution_time_seconds=time.time() - start,
            )

        return TestResult(
            test_name=self.name,
            status=status,
            findings=findings,
            execution_time_seconds=time.time() - start,
            output_log=result.stdout + result.stderr,
            metadata={"tool": "bandit", "scanned_paths": [str(src_dir)]},
        )


class SCATest:
    """Plugin: Auditoría de dependencias (Trivy fs mode)"""

    name = "sca"
    description = "Escanea dependencias del proyecto en busca de vulnerabilidades conocidas (CVEs)"

    def __init__(self, severity_filter: list[TestSeverity] = None):
        self.severity_filter = severity_filter or [
            TestSeverity.HIGH,
            TestSeverity.CRITICAL,
        ]

    def is_applicable(self, project_path: Path) -> bool:
        lock_files = [
            "requirements.txt",
            "requirements.lock.txt",
            "pyproject.toml",
            "poetry.lock",
        ]
        return any((project_path / f).exists() for f in lock_files)

    def execute(self, project_path: Path, **kwargs) -> TestResult:
        import time

        start = time.time()
        findings = []

        try:
            severity_arg = ",".join(s.value.upper() for s in self.severity_filter)
            cmd = [
                "trivy",
                "fs",
                str(project_path),
                "--scanners",
                "vuln",
                "--severity",
                severity_arg,
                "--format",
                "json",
                "--no-progress",
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600, cwd=project_path
            )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    for res in data.get("Results", []):
                        for vuln in res.get("Vulnerabilities", []):
                            severity_map = {
                                "CRITICAL": TestSeverity.CRITICAL,
                                "HIGH": TestSeverity.HIGH,
                                "MEDIUM": TestSeverity.MEDIUM,
                                "LOW": TestSeverity.LOW,
                            }
                            findings.append(
                                SecurityFinding(
                                    id=vuln.get("VulnerabilityID", "UNKNOWN"),
                                    title=vuln.get(
                                        "Title", "Vulnerabilidad en dependencia"
                                    ),
                                    severity=severity_map.get(
                                        vuln.get("Severity", "UNKNOWN"),
                                        TestSeverity.UNKNOWN,
                                    ),
                                    description=vuln.get("Description", ""),
                                    location=f"{res.get('Target', 'unknown')}:{vuln.get('PkgName', '')}",
                                    cve=vuln.get("VulnerabilityID"),
                                    fix_recommendation=f"Actualizar a {vuln.get('FixedVersion', 'versión parcheada')}",
                                    raw_data=vuln,
                                )
                            )
                except json.JSONDecodeError:
                    pass

            has_critical = any(f.severity == TestSeverity.CRITICAL for f in findings)
            has_high = any(f.severity == TestSeverity.HIGH for f in findings)
            status = (
                TestStatus.FAILED
                if has_critical
                else (TestStatus.WARNING if has_high else TestStatus.PASSED)
            )

        except FileNotFoundError:
            return TestResult(
                test_name=self.name,
                status=TestStatus.SKIPPED,
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return TestResult(
                test_name=self.name,
                status=TestStatus.ERROR,
                output_log=str(e),
                execution_time_seconds=time.time() - start,
            )

        return TestResult(
            test_name=self.name,
            status=status,
            findings=findings,
            execution_time_seconds=time.time() - start,
            output_log=result.stdout + result.stderr,
            metadata={
                "tool": "trivy",
                "severity_filter": [s.value for s in self.severity_filter],
            },
        )


class ImageScanTest:
    """Plugin: Escaneo de imagen Docker/entorno (Trivy image/fs)"""

    name = "image-scan"
    description = "Audita vulnerabilidades en el entorno de ejecución o imagen Docker"

    def __init__(self, mode: str = "fs", image_name: str | None = None):
        self.mode = mode  # "fs" o "image"
        self.image_name = image_name

    def is_applicable(self, project_path: Path) -> bool:
        """¿Esta prueba aplica para este proyecto?"""
        if self.mode == "image" and not self.image_name:
            return False
        return True

    def execute(self, project_path: Path, **kwargs) -> TestResult:
        import time

        start = time.time()
        findings = []

        try:
            if self.mode == "image" and self.image_name:
                cmd = [
                    "trivy",
                    "image",
                    self.image_name,
                    "--severity",
                    "HIGH,CRITICAL",
                    "--format",
                    "json",
                    "--no-progress",
                ]
            else:
                cmd = [
                    "trivy",
                    "fs",
                    str(project_path),
                    "--scanners",
                    "vuln",
                    "--severity",
                    "HIGH,CRITICAL",
                    "--format",
                    "json",
                    "--no-progress",
                ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=600, cwd=project_path
            )

            if result.returncode == 0 and result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    for res in data.get("Results", []):
                        for vuln in res.get("Vulnerabilities", []):
                            findings.append(
                                SecurityFinding(
                                    id=vuln.get("VulnerabilityID", "UNKNOWN"),
                                    title=vuln.get(
                                        "Title", "Vulnerabilidad de sistema"
                                    ),
                                    severity=(
                                        TestSeverity.HIGH
                                        if vuln.get("Severity") in ["HIGH", "CRITICAL"]
                                        else TestSeverity.MEDIUM
                                    ),
                                    description=vuln.get("Description", ""),
                                    location=f"{res.get('Target', 'unknown')}:{vuln.get('PkgName', '')}",
                                    cve=vuln.get("VulnerabilityID"),
                                    fix_recommendation="Actualizar paquete o aplicar parche de seguridad",
                                    raw_data=vuln,
                                )
                            )
                except json.JSONDecodeError:
                    pass

            status = (
                TestStatus.FAILED
                if any(f.severity == TestSeverity.CRITICAL for f in findings)
                else TestStatus.PASSED
            )

        except FileNotFoundError:
            return TestResult(
                test_name=self.name,
                status=TestStatus.SKIPPED,
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return TestResult(
                test_name=self.name,
                status=TestStatus.ERROR,
                output_log=str(e),
                execution_time_seconds=time.time() - start,
            )

        return TestResult(
            test_name=self.name,
            status=status,
            findings=findings,
            execution_time_seconds=time.time() - start,
            output_log=result.stdout + result.stderr,
            metadata={"tool": "trivy", "mode": self.mode, "image": self.image_name},
        )


class SecurityTestRegistry:
    """Registro centralizado de plugins de pruebas de seguridad"""

    _plugins: dict[str, type[SecurityTestPlugin]] = {}

    @classmethod
    def register(
        cls, plugin_class: type[SecurityTestPlugin]
    ) -> type[SecurityTestPlugin]:
        """Decorator para registrar un plugin automáticamente"""
        if not hasattr(plugin_class, "name") or not plugin_class.name:
            raise ValueError(
                f"Plugin {plugin_class.__name__} debe tener atributo 'name'"
            )
        cls._plugins[plugin_class.name] = plugin_class
        logger.info(f"🔌 Plugin registrado: {plugin_class.name}")
        return plugin_class

    @classmethod
    def get(cls, name: str, **kwargs) -> SecurityTestPlugin | None:
        """Instancia un plugin por nombre con configuración opcional"""
        plugin_class = cls._plugins.get(name)
        if not plugin_class:
            logger.warning(
                f"⚠️ Plugin '{name}' no registrado. Plugins disponibles: {list(cls._plugins.keys())}"
            )
            return None
        return plugin_class(**kwargs) if kwargs else plugin_class()

    @classmethod
    def list_available(cls) -> list[str]:
        """Lista nombres de plugins disponibles"""
        return list(cls._plugins.keys())


# Registrar plugins por defecto
SecurityTestRegistry.register(SecretsTest)
SecurityTestRegistry.register(SASTTest)
SecurityTestRegistry.register(SCATest)
SecurityTestRegistry.register(ImageScanTest)


# ─────────────────────────────────────────────────────────────────────────────
# ORCHESTRATOR PRINCIPAL: Coordina todo el flujo
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class OrchestratorConfig:
    """Configuración centralizada del orchestrator"""

    project_path: Path
    output_dir: Path = Path("reports")
    enabled_tests: list[str] = field(
        default_factory=lambda: ["secrets", "sast", "sca", "image-scan", "licenses"]
    )
    severity_threshold: TestSeverity = (
        TestSeverity.HIGH
    )  # Fallar si hay >= a este nivel
    export_formats: list[str] = field(
        default_factory=lambda: ["console", "json", "html"]
    )  # console, json, html
    fail_fast: bool = False  # Detener ejecución ante primer fallo crítico
    use_rich: bool = True


class DevSecOpsOrchestrator:
    """Orquestador principal de pruebas de seguridad."""

    def __init__(self, config: OrchestratorConfig):
        self.config = config
        self.report_engine = ReportEngine(use_rich=config.use_rich)
        self.results: list[TestResult] = []

    def _execute_test(self, plugin: SecurityTestPlugin) -> TestResult:
        logger.info(f"🔍 Ejecutando: {plugin.name} — {plugin.description}")
        if not plugin.is_applicable(self.config.project_path):
            logger.info(f"⤷ Saltando {plugin.name}: no aplicable para este proyecto")
            return TestResult(test_name=plugin.name, status=TestStatus.SKIPPED)
        return plugin.execute(self.config.project_path)

    def _should_fail(self, result: TestResult) -> bool:
        if not self.config.fail_fast:
            return False
        if result.status == TestStatus.ERROR:
            return True
        return any(
            f.severity.value <= self.config.severity_threshold.value
            for f in result.findings
        )

    def _ensure_gitignore_protection(self) -> None:
        """Inyecta reglas en el .gitignore para evitar que los reportes se suban al repo."""
        gitignore_path = self.config.project_path / ".gitignore"
        output_dir_name = self.config.output_dir.name

        ignore_block = (
            "\n# 🛡️ DevSecOps Orchestrator - Auto-generated reports\n"
            f"{output_dir_name}/\n"
            "security-report-*.json\n"
            "security-report-*.html\n"
        )

        if not gitignore_path.exists():
            gitignore_path.write_text(ignore_block.lstrip())
            logger.info("📄 Archivo .gitignore creado (Reglas de DevSecOps aplicadas).")
            return

        content = gitignore_path.read_text(encoding="utf-8")
        if (
            "DevSecOps Orchestrator" not in content
            and f"{output_dir_name}/" not in content
        ):
            with gitignore_path.open("a", encoding="utf-8") as f:
                if content and not content.endswith("\n"):
                    f.write("\n")
                f.write(ignore_block)
            logger.info(
                "🛡️ Archivo .gitignore actualizado (Protección de artefactos añadida)."
            )

    def run(self) -> bool:
        self._ensure_gitignore_protection()

        self.report_engine.print_header(
            "🛡️ DevSecOps Security Pipeline",
            f"Proyecto: {self.config.project_path.name} | {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        )

        all_passed = True

        for test_name in self.config.enabled_tests:
            plugin = SecurityTestRegistry.get(test_name)
            if not plugin:
                logger.warning(f"⚠️ Plugin '{test_name}' no disponible, saltando")
                continue

            result = self._execute_test(plugin)
            self.results.append(result)
            self.report_engine.print_test_result(result)

            if result.status == TestStatus.FAILED or result.has_critical_issues:
                all_passed = False

            if self._should_fail(result):
                logger.error(
                    f"🛑 Fail-fast activado: deteniendo ejecución por {test_name}"
                )
                break

        self.report_engine.print_summary(self.results)

        if "json" in self.config.export_formats:
            json_path = (
                self.config.output_dir
                / f"security-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
            )
            self.report_engine.export_json(self.results, json_path)

        if "html" in self.config.export_formats:
            html_path = (
                self.config.output_dir
                / f"security-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
            )
            self.report_engine.export_html(self.results, html_path)

        if all_passed:
            logger.info("✅ Todas las pruebas de seguridad aprobadas")
        else:
            logger.warning("⚠️ Algunas pruebas revelaron problemas de seguridad")

        return all_passed

    @property
    def summary(self) -> dict[str, Any]:
        return {
            "total_tests": len(self.results),
            "passed": sum(1 for r in self.results if r.status == TestStatus.PASSED),
            "failed": sum(1 for r in self.results if r.status == TestStatus.FAILED),
            "total_findings": sum(len(r.findings) for r in self.results),
            "critical": sum(
                sum(1 for f in r.findings if f.severity == TestSeverity.CRITICAL)
                for r in self.results
            ),
            "high": sum(
                sum(1 for f in r.findings if f.severity == TestSeverity.HIGH)
                for r in self.results
            ),
            "results": [r.to_dict() for r in self.results],
        }


@SecurityTestRegistry.register
class LicenseComplianceTest:
    """Plugin personalizado: Verifica licencias de dependencias en Python"""

    name = "licenses"
    description = "Audita que las dependencias no usen licencias restrictivas (ej. GPL)"

    def is_applicable(self, project_path: Path) -> bool:
        return (project_path / "requirements.txt").exists()

    def execute(self, project_path: Path, **kwargs) -> TestResult:
        import time

        start = time.time()
        findings = []
        forbidden_licenses = ["GPL", "AGPL", "RESTRICTIVE"]

        try:
            cmd = ["pip-licenses", "--format=json"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=project_path
            )

            if result.returncode == 0:
                packages = json.loads(result.stdout)
                for pkg in packages:
                    license_name = pkg.get("License", "UNKNOWN")
                    if any(bad in license_name.upper() for bad in forbidden_licenses):
                        findings.append(
                            SecurityFinding(
                                id=f"LIC-{pkg.get('Name')}",
                                title=f"Licencia restrictiva detectada: {license_name}",
                                severity=TestSeverity.MEDIUM,
                                description=f"El paquete usa una licencia ({license_name}) que requiere revisión legal.",
                                location=f"{pkg.get('Name')}=={pkg.get('Version')}",
                                fix_recommendation="Buscar una alternativa con licencia MIT, Apache o BSD.",
                            )
                        )
            status = TestStatus.WARNING if findings else TestStatus.PASSED

        except FileNotFoundError:
            return TestResult(
                self.name,
                TestStatus.SKIPPED,
                output_log="Herramienta no instalada",
                execution_time_seconds=time.time() - start,
            )
        except Exception as e:
            return TestResult(
                self.name,
                TestStatus.ERROR,
                output_log=str(e),
                execution_time_seconds=time.time() - start,
            )

        return TestResult(
            test_name=self.name,
            status=status,
            findings=findings,
            execution_time_seconds=time.time() - start,
            metadata={"tool": "pip-licenses"},
        )


# === 🛡️ EJECUCIÓN PARA CI/CD (GitHub Actions / Pipelines) ===
if __name__ == "__main__":
    # Si este script se ejecuta directamente en CI/CD, lo configuramos
    # para escanear el root de ejecución (donde clona GitHub Actions).
    config = OrchestratorConfig(
        project_path=Path(os.getcwd()),
        enabled_tests=["secrets", "sast", "sca", "image-scan", "licenses"],
    )
    orchestrator = DevSecOpsOrchestrator(config)
    success = orchestrator.run()

    # Fundamental para CI/CD: Rompe el build si las pruebas no son exitosas
    if not success:
        sys.exit(1)
