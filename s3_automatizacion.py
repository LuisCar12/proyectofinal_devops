#!/usr/bin/env python3
"""
s3_automatizacion.py
Operaciones S3 con boto3:
  1. Crea un archivo de prueba local.
  2. Lo sube al bucket S3 en la carpeta pruebas/.
  3. Lista todos los objetos del bucket con nombre, tamano y fecha de modificacion.

Uso: python3 s3_automatizacion.py
El bucket se descubre automaticamente buscando el creado por CloudFormation.
"""

from datetime import datetime
from pathlib import Path
import sys
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
PREFIJO_BUCKET = "devops-bucket"
ARCHIVO_LOCAL = Path("/tmp/archivo_prueba.txt")
KEY_S3 = "pruebas/archivo_prueba.txt"


def descubrir_bucket(s3):
    """Busca el primer bucket cuyo nombre empieza por el prefijo definido."""
    buckets = s3.list_buckets().get("Buckets", [])
    candidatos = [b["Name"] for b in buckets if b["Name"].startswith(PREFIJO_BUCKET)]
    if not candidatos:
        return None
    return candidatos[0]


def crear_archivo_local():
    contenido = (
        f"Archivo de prueba DevOps\n"
        f"Generado: {datetime.utcnow().isoformat()}Z\n"
        f"Proposito: validar subida a S3.\n"
    )
    ARCHIVO_LOCAL.write_text(contenido)
    print(f"[1/3] Archivo local creado: {ARCHIVO_LOCAL}")


def subir_a_s3(s3, bucket):
    s3.upload_file(str(ARCHIVO_LOCAL), bucket, KEY_S3)
    print(f"[2/3] Subido a s3://{bucket}/{KEY_S3}")


def listar_objetos(s3, bucket):
    print(f"[3/3] Objetos en s3://{bucket}/")
    paginador = s3.get_paginator("list_objects_v2")
    total = 0
    for pagina in paginador.paginate(Bucket=bucket):
        for obj in pagina.get("Contents", []):
            print(
                f"  - {obj['Key']} | {obj['Size']} bytes | "
                f"modificado: {obj['LastModified'].isoformat()}"
            )
            total += 1
    if total == 0:
        print("  (vacio)")
    print(f"  Total: {total} objetos")


def main():
    s3 = boto3.client("s3", region_name=REGION)

    bucket = descubrir_bucket(s3)
    if not bucket:
        print(
            f"ERROR: no se encontro un bucket con prefijo '{PREFIJO_BUCKET}'.\n"
            "Despliega primero la plantilla CloudFormation (template.yaml)."
        )
        sys.exit(1)

    print(f"Usando bucket: {bucket}\n")

    try:
        crear_archivo_local()
        subir_a_s3(s3, bucket)
        listar_objetos(s3, bucket)
    except ClientError as e:
        print(f"Error en operacion S3: {e}")
        sys.exit(1)

    print("\n=== Operaciones S3 completadas ===")


if __name__ == "__main__":
    main()
