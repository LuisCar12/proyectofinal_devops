#!/bin/bash
# setup.sh - Instala dependencias del proyecto DevOps
# Uso: bash setup.sh

set -e

echo "=== Iniciando setup del entorno DevOps ==="

# Actualizar paquetes del sistema
echo "[1/4] Actualizando paquetes del sistema..."
sudo dnf update -y

# Asegurar pip y python3
echo "[2/4] Verificando python3 y pip..."
sudo dnf install -y python3 python3-pip

# Instalar boto3 y dependencias Python
echo "[3/4] Instalando boto3 y librerias Python..."
pip3 install --user boto3 botocore flask

# Iniciar Docker
echo "[4/4] Iniciando servicio Docker..."
sudo service docker start || true
sudo usermod -aG docker ec2-user || true

echo "=== Setup completado ==="
echo "Verifica con: aws sts get-caller-identity"
echo "Verifica boto3 con: python3 -c 'import boto3; print(boto3.__version__)'"
