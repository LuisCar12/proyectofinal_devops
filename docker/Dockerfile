# Multi-stage build: imagen final mas pequena al excluir herramientas de instalacion.

# --- Stage 1: builder ---
FROM python:3.11-slim AS builder

WORKDIR /build

COPY requirements.txt .

# Instalar dependencias en una carpeta aislada para copiarla despues.
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# --- Stage 2: imagen final ---
FROM python:3.11-slim

WORKDIR /app

# Copiar solo las dependencias ya instaladas, sin las herramientas de pip.
COPY --from=builder /install /usr/local

# Copiar el codigo de la aplicacion.
COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]
