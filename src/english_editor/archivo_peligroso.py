import subprocess
import yaml

def ataque_critico(datos_usuario):
    # 🚨 VULNERABILIDAD ALTA 1: Inyección de Comandos (Command Injection)
    # Ejecutar comandos de consola concatenando texto de usuarios es letal.
    subprocess.Popen(datos_usuario, shell=True)
    
    # 🚨 VULNERABILIDAD ALTA 2: Deserialización Insegura
    # Leer un YAML de esta forma permite a un atacante ejecutar código remoto.
    yaml.load(datos_usuario)