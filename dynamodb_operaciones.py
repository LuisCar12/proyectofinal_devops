#!/usr/bin/env python3
"""
dynamodb_operaciones.py
CRUD basico en DynamoDB con boto3:
  1. Crear tabla 'devops-tabla' con clave primaria 'id' (String), modo PAY_PER_REQUEST.
  2. Insertar un registro con id, nombre y status.
  3. Modificar el campo status con update_item usando ExpressionAttributeNames
     (status es palabra reservada en DynamoDB).
  4. Eliminar el registro con delete_item.

Uso: python3 dynamodb_operaciones.py
"""

import time
import boto3
from botocore.exceptions import ClientError

REGION = "us-east-1"
TABLA = "devops-tabla"
ITEM_ID = "registro-001"


def crear_tabla(cliente):
    print(f"[1/4] Creando tabla '{TABLA}'...")
    try:
        cliente.create_table(
            TableName=TABLA,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        cliente.get_waiter("table_exists").wait(TableName=TABLA)
        print(f"  Tabla '{TABLA}' creada y activa.")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceInUseException":
            print(f"  La tabla '{TABLA}' ya existe, continuando.")
        else:
            raise


def insertar_registro(tabla):
    print(f"[2/4] Insertando registro id={ITEM_ID}...")
    tabla.put_item(
        Item={
            "id": ITEM_ID,
            "nombre": "Servidor Web Principal",
            "status": "activo",
        }
    )
    print("  Registro insertado.")


def actualizar_status(tabla):
    """status es palabra reservada en DynamoDB, hay que usar ExpressionAttributeNames."""
    print(f"[3/4] Actualizando status del registro id={ITEM_ID}...")
    tabla.update_item(
        Key={"id": ITEM_ID},
        UpdateExpression="SET #s = :nuevo",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={":nuevo": "mantenimiento"},
    )

    actualizado = tabla.get_item(Key={"id": ITEM_ID}).get("Item")
    print(f"  Registro tras update: {actualizado}")


def eliminar_registro(tabla):
    print(f"[4/4] Eliminando registro id={ITEM_ID}...")
    tabla.delete_item(Key={"id": ITEM_ID})
    print("  Registro eliminado.")


def main():
    cliente = boto3.client("dynamodb", region_name=REGION)
    recurso = boto3.resource("dynamodb", region_name=REGION)

    crear_tabla(cliente)

    # Pequena espera defensiva por si la tabla recien creada aun no esta lista para escritura
    time.sleep(2)

    tabla = recurso.Table(TABLA)
    insertar_registro(tabla)
    actualizar_status(tabla)
    eliminar_registro(tabla)

    print("\n=== Operaciones DynamoDB completadas ===")
    print(f"Nota: la tabla '{TABLA}' permanece creada. Para borrarla:")
    print(f"  aws dynamodb delete-table --table-name {TABLA} --region {REGION}")


if __name__ == "__main__":
    main()
