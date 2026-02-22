def funcion_insegura():
    # 🚨 VULNERABILIDAD 1 (SAST): Contraseña escrita directamente en el código (Hardcoded password)
    # Bandit detectará esto y lanzará una alerta.
    password_base_datos = "admin12345"
    
    # 🚨 VULNERABILIDAD 2 (SAST): Uso de eval()
    # Ejecutar código como texto es una de las peores prácticas de seguridad en Python.
    entrada_usuario = "2 + 2"
    resultado = eval(entrada_usuario)
    
    # 🚨 VULNERABILIDAD 3 (Secretos): Un token falso de AWS.
    # Gitleaks escanea buscando patrones matemáticos de tokens reales. Este es un patrón de prueba de AWS.
    aws_access_key_id = "AKIAIOSFODNN7EXAMPLE"
    
    return resultado