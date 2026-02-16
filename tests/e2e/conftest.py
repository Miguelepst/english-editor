# tests/e2e/conftest.py
import os

import pytest


@pytest.fixture
def big_file_factory(tmp_path):
    """
    Factory para crear archivos 'Sparse' (huecos) que simulan ser gigantes.
    Permite probar la lógica de lectura de cabecera/cola sin gastar disco real.
    """

    def _create_sparse_file(filename: str, size_gb: float):
        filepath = tmp_path / filename
        size_bytes = int(size_gb * 1024 * 1024 * 1024)

        with open(filepath, "wb") as f:
            # 1. Escribir cabecera real (para el hash inicial)
            f.write(b"HEADER_" + os.urandom(100))

            # 2. Saltar hasta casi el final (Sparse seek)
            # Esto hace que el archivo tenga "tamaño lógico" pero no ocupe espacio físico intermedio
            f.seek(size_bytes - 100)

            # 3. Escribir cola real (para validar lectura de fin de archivo)
            f.write(b"FOOTER_" + os.urandom(90))

        return filepath

    return _create_sparse_file
