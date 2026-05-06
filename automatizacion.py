#!/usr/bin/env python3
"""
automatizacion.py
Script de automatizacion DevOps con boto3.

Funciones:
  1. Listar instancias EC2 (ID, tipo, estado).
  2. Reporte de uso de CPU de las ultimas 24 horas (CloudWatch).
  3. Listar buckets S3 y sus objetos.
  4. Listar grupos de Auto Scaling con su capacidad min/max/deseada.

Uso: python3 automatizacion.py
"""

from datetime import datetime, timedelta, timezone
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"


def listar_instancias_ec2():
    print("\n=== Instancias EC2 ===")
    ec2 = boto3.client("ec2", region_name=REGION)
    try:
        respuesta = ec2.describe_instances()
    except ClientError as e:
        print(f"Error consultando EC2: {e}")
        return []

    instancias = []
    for reserva in respuesta.get("Reservations", []):
        for inst in reserva.get("Instances", []):
            datos = {
                "id": inst["InstanceId"],
                "tipo": inst["InstanceType"],
                "estado": inst["State"]["Name"],
            }
            instancias.append(datos)
            print(f"  ID: {datos['id']} | Tipo: {datos['tipo']} | Estado: {datos['estado']}")

    if not instancias:
        print("  (sin instancias)")
    return instancias


def reporte_cpu_ec2(instancias):
    print("\n=== Reporte de CPU - ultimas 24h ===")
    cw = boto3.client("cloudwatch", region_name=REGION)
    fin = datetime.now(timezone.utc)
    inicio = fin - timedelta(hours=24)

    en_ejecucion = [i for i in instancias if i["estado"] == "running"]
    if not en_ejecucion:
        print("  No hay instancias en ejecucion.")
        return

    for inst in en_ejecucion:
        try:
            datos = cw.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": inst["id"]}],
                StartTime=inicio,
                EndTime=fin,
                Period=3600,
                Statistics=["Average", "Maximum"],
            )
        except ClientError as e:
            print(f"  Error obteniendo metricas de {inst['id']}: {e}")
            continue

        puntos = sorted(datos.get("Datapoints", []), key=lambda x: x["Timestamp"])
        if not puntos:
            print(f"  {inst['id']}: sin datos en las ultimas 24h")
            continue

        promedio = sum(p["Average"] for p in puntos) / len(puntos)
        pico = max(p["Maximum"] for p in puntos)
        print(f"  {inst['id']}: promedio {promedio:.2f}% | pico {pico:.2f}% | muestras {len(puntos)}")


def listar_buckets_s3():
    print("\n=== Buckets S3 ===")
    s3 = boto3.client("s3", region_name=REGION)
    try:
        buckets = s3.list_buckets().get("Buckets", [])
    except ClientError as e:
        print(f"Error consultando S3: {e}")
        return

    if not buckets:
        print("  (sin buckets)")
        return

    for bucket in buckets:
        nombre = bucket["Name"]
        print(f"\n  Bucket: {nombre}")
        try:
            objetos = s3.list_objects_v2(Bucket=nombre).get("Contents", [])
            if not objetos:
                print("    (vacio)")
            else:
                for obj in objetos[:10]:
                    print(f"    - {obj['Key']} ({obj['Size']} bytes)")
                if len(objetos) > 10:
                    print(f"    ... y {len(objetos) - 10} objetos mas")
        except ClientError as e:
            print(f"    Error listando objetos: {e}")


def listar_auto_scaling():
    print("\n=== Grupos Auto Scaling ===")
    asg = boto3.client("autoscaling", region_name=REGION)
    try:
        grupos = asg.describe_auto_scaling_groups().get("AutoScalingGroups", [])
    except ClientError as e:
        print(f"Error consultando Auto Scaling: {e}")
        return

    if not grupos:
        print("  (sin grupos Auto Scaling)")
        return

    for g in grupos:
        print(
            f"  Nombre: {g['AutoScalingGroupName']} | "
            f"min: {g['MinSize']} | max: {g['MaxSize']} | deseada: {g['DesiredCapacity']}"
        )


def main():
    print("=" * 50)
    print("  Automatizacion DevOps - boto3")
    print("=" * 50)

    instancias = listar_instancias_ec2()
    reporte_cpu_ec2(instancias)
    listar_buckets_s3()
    listar_auto_scaling()

    print("\n=== Fin del reporte ===")


if __name__ == "__main__":
    main()
