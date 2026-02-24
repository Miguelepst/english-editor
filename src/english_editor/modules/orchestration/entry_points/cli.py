# src/english_editor/modules/orchestration/entry_points/cli.py
"""
Interfaz de Línea de Comandos (CLI) para el Módulo de Orquestación.

Arquitectura: Interface Adapter
Responsabilidad: Traducir comandos de terminal a casos de uso del dominio.
"""

import argparse
import os
import sys

# Ajuste de path para ejecución directa
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from english_editor.modules.orchestration.application.use_cases import JobOrchestrator
from english_editor.modules.orchestration.domain.value_objects import JobStatus
from english_editor.modules.orchestration.infrastructure.adapters import (
    JsonFileRepository,
    LocalFileSystemAdapter,
)


def main():
    parser = argparse.ArgumentParser(
        description="Orquestador de Trabajos English Editor"
    )

    # Argumentos
    parser.add_argument(
        "--input", "-i", required=True, help="Archivo o directorio de entrada"
    )
    parser.add_argument("--output", "-o", required=True, help="Directorio de salida")
    parser.add_argument(
        "--db", default="./checkpoints.json", help="Ruta al archivo JSON de estado"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Forzar reprocesamiento si existe output",
    )

    args = parser.parse_args()

    # 1. Composición (Wiring)
    # Aquí ensamblamos las dependencias reales
    repo = JsonFileRepository(args.db)
    fs = LocalFileSystemAdapter()
    orchestrator = JobOrchestrator(repo, fs)

    print("🚀 Iniciando escaneo de orquestación...")
    print(f"📂 Entrada: {args.input}")
    print(f"💾 DB Estado: {args.db}\n")

    # 2. Ejecución del Caso de Uso
    try:
        # prepare_jobs() solo acepta input_dir y output_dir
        # El flag --force se maneja internamente por el orquestador al detectar archivos existentes
        jobs = list(
            orchestrator.prepare_jobs(input_path=args.input, output_dir=args.output)
        )

        # La firma de la funcion:
        # def prepare_jobs(self, input_path: str, output_dir: str, force: bool = False) -> Iterator[ProcessingJob]:

        # 2. Ejecución del Caso de Uso
        # try:
        # El orquestador devuelve un generador, iteramos para ejecutar la lógica
        # jobs = list(orchestrator.prepare_jobs(
        #    input_path=args.input,
        #    output_path=args.output,
        #    force=args.force
        # ))

        # 3. Presentación (View Logic)
        if not jobs:
            print(
                "✨ No hay trabajos pendientes (Todo está al día o la carpeta está vacía)."
            )
            return

        print(f"📋 Se encontraron {len(jobs)} trabajos activos:\n")

        # Encabezados de tabla simple
        print(f"{'ESTADO':<15} | {'PROGRESO':<10} | {'ARCHIVO'}")
        print("-" * 60)

        for job in jobs:
            status_icon = (
                "🟢"
                if job.status == JobStatus.COMPLETED
                else "🟡" if job.status == JobStatus.IN_PROGRESS else "⚪"
            )
            progress = f"{job.progress_count} segm"

            print(
                f"{status_icon} {job.status.name:<12} | {progress:<10} | {job.source.filename}"
            )

            if job.status == JobStatus.IN_PROGRESS:
                last_ckpt = (
                    job.get_checkpoints_copy()[-1]
                    if job.get_checkpoints_copy()
                    else "N/A"
                )
                print(f"   ↳ 🔄 Reanudando desde: {last_ckpt}")

    except Exception as e:
        print(f"❌ Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
