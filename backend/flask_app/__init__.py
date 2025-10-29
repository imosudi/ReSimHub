# backend/flask_app/__init__.py
from flask import Flask, jsonify
from .routes.training_bridge import bridge_bp
import requests

app = Flask(__name__)
app.register_blueprint(bridge_bp)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "flask"})

@app.route("/fastapi-health")
def fastapi_health():
    try:
        res = requests.get("http://127.0.0.1:8000/health", timeout=2)
        return jsonify({"fastapi": res.json()})
    except requests.exceptions.RequestException:
        return jsonify({"error": "FastAPI service not reachable"}), 503
