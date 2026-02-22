def funcion_segura(datos_usuario: str) -> bool:
    """
    Procesa los datos del usuario de forma segura.
    
    Esta función reemplaza las vulnerabilidades de ejecución
    de comandos y deserialización por un manejo de strings seguro.
    """
    texto_limpio: str = str(datos_usuario).strip()
    
    print(f"Procesando datos de forma segura: {texto_limpio}")
    return True
