# backend/flask_app/__init__.py
from flask import Flask, jsonify
import requests
from .routes.training_bridge import bridge_bp
from .services.api_proxy import FastAPIProxy

app = Flask(__name__)

app.register_blueprint(bridge_bp)

@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "flask"})

@app.route("/fastapi-health")
def fastapi_health():
    try:
        res = requests.get("http://localhost:8000/health", timeout=2)
        return jsonify({"flask_bridge": res.json()})
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "FastAPI service not reachable"}), 503
