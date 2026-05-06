#!/bin/bash
# usuarios.sh - Gestiona usuarios y permisos en el entorno
# Uso: sudo bash usuarios.sh

set -e

USUARIO="devops_user"
HOME_DIR="/home/$USUARIO"

echo "=== Creando usuario $USUARIO ==="

# Crear el usuario si no existe
if id "$USUARIO" &>/dev/null; then
    echo "Usuario $USUARIO ya existe, saltando creacion."
else
    sudo useradd -m -s /bin/bash "$USUARIO"
    echo "Usuario $USUARIO creado."
fi

# Crear grupo devops si no existe y agregar al usuario
if ! getent group devops >/dev/null; then
    sudo groupadd devops
    echo "Grupo devops creado."
fi
sudo usermod -aG devops "$USUARIO"

# Permisos sobre la carpeta del entorno Cloud9
if [ -d "/home/ec2-user/environment" ]; then
    sudo chown -R "$USUARIO:devops" /home/ec2-user/environment
    sudo chmod -R 775 /home/ec2-user/environment
    echo "Permisos asignados a $USUARIO sobre ~/environment."
fi

# Permitir sudo sin contrasena para tareas DevOps (entorno controlado del lab)
SUDOERS_FILE="/etc/sudoers.d/devops_user"
if [ ! -f "$SUDOERS_FILE" ]; then
    echo "$USUARIO ALL=(ALL) NOPASSWD:ALL" | sudo tee "$SUDOERS_FILE" >/dev/null
    sudo chmod 440 "$SUDOERS_FILE"
    echo "Sudoers configurado para $USUARIO."
fi

# IMPORTANTE: restaurar permisos a ec2-user para que pueda seguir trabajando en Cloud9
echo "Restaurando permisos de ~/environment a ec2-user..."
sudo chown -R ec2-user:ec2-user ~/environment

echo "=== Gestion de usuarios completada ==="
