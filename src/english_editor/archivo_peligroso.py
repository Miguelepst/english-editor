def funcion_insegura():
    # 🚨 VULNERABILIDAD 1 (SAST): Contraseña escrita directamente en el código (Hardcoded password)
    # Bandit detectará esto y lanzará una alerta.
    # ✅ Agregar noqa para suprimir la alerta de Ruff
    password_base_datos = "admin12345"  # noqa: F841

    # 🚨 VULNERABILIDAD 2 (SAST): Uso de eval()
    # Ejecutar código como texto es una de las peores prácticas de seguridad en Python.
    entrada_usuario = "2 + 2"
    resultado = eval(entrada_usuario)  # noqa: S307

    # 🚨 VULNERABILIDAD 3 (Secretos): Un token falso de AWS.
    # Gitleaks escanea buscando patrones matemáticos de tokens reales. Este es un patrón de prueba de AWS.
    aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"  # noqa: F841
    return resultado
