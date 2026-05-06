"""
lambda_function.py
Microservicio DevOps - retorna un mensaje aleatorio del proyecto.
"""

import json
import random


def lambda_handler(event, context):
    mensajes = [
        "DevOps une desarrollo y operaciones para entregas mas rapidas.",
        "La automatizacion reduce errores humanos y acelera despliegues.",
        "El monitoreo continuo es clave para detectar problemas a tiempo.",
        "CI/CD permite entregar valor al usuario de forma predecible.",
        "La infraestructura como codigo asegura entornos reproducibles.",
        "DevSecOps integra la seguridad en cada etapa del pipeline.",
    ]

    cuerpo = {
        "mensaje": random.choice(mensajes),
        "servicio": "microservicio-devops",
    }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(cuerpo),
    }
