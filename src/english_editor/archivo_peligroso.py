def funcion_segura(datos_usuario):
    # ✅ PRÁCTICA SEGURA: En lugar de ejecutar comandos de consola (shell=True)
    # o deserializar YAMLs peligrosos, simplemente procesamos el texto.
    texto_limpio = str(datos_usuario).strip()
    
    print(f"Procesando datos de forma segura: {texto_limpio}")
    return True