#!/bin/bash
# limpieza_logs.sh - Limpia archivos de log antiguos
# Programado con cron para ejecutarse diariamente a medianoche
# Crontab sugerido: 0 0 * * * /home/ec2-user/environment/limpieza_logs.sh

LOG_DIR="/var/log"
DIAS_RETENCION=7
REPORTE="/tmp/limpieza_logs_$(date +%Y%m%d).log"

echo "=== Limpieza de logs - $(date) ===" | tee "$REPORTE"

# Borrar archivos .log con mas de N dias
ARCHIVOS=$(sudo find "$LOG_DIR" -type f -name "*.log" -mtime +$DIAS_RETENCION 2>/dev/null)

if [ -z "$ARCHIVOS" ]; then
    echo "No hay logs mayores a $DIAS_RETENCION dias para eliminar." | tee -a "$REPORTE"
else
    echo "Eliminando logs con mas de $DIAS_RETENCION dias:" | tee -a "$REPORTE"
    echo "$ARCHIVOS" | tee -a "$REPORTE"
    sudo find "$LOG_DIR" -type f -name "*.log" -mtime +$DIAS_RETENCION -delete
fi

# Truncar logs activos muy grandes (>100MB)
sudo find "$LOG_DIR" -type f -name "*.log" -size +100M -exec sudo truncate -s 0 {} \; 2>/dev/null || true

echo "Limpieza finalizada a las $(date)" | tee -a "$REPORTE"
