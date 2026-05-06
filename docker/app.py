"""
app.py - Aplicacion web Flask para el proyecto DevOps.
Responde en el puerto 5000 con un mensaje JSON.
"""

from flask import Flask, jsonify

app = Flask(__name__)


@app.route("/")
def home():
    return jsonify(
        mensaje="Hola desde DevOps - Soluciones Tecnologicas del Futuro",
        servicio="flask-web",
        estado="ok",
    )


@app.route("/health")
def health():
    return jsonify(status="healthy"), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
