"""
ReSimHub Flask Web Application.

Provides the initial public-facing interface and API bridge routes.
The Flask application instance is directly instantiated at module level
without an application factory.
"""

import os
from flask import Flask, jsonify, render_template
import requests

from .routes.training_bridge import bridge_bp

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://127.0.0.1:8000")

# Initialise Flask application directly at module level (no application factory)
app = Flask(__name__, template_folder="templates")
app.register_blueprint(bridge_bp)


@app.route("/")
def home():
    """
    Render the initial public-facing home page.

    Serves a blank HTML document devoid of UI/UX styling or components,
    reserved for downstream design implementation.
    """
    return render_template("index.html")


@app.route("/health")
def health():
    """Return health status of the Flask application service."""
    return jsonify({"status": "ok", "service": "flask"})


@app.route("/fastapi-health")
def fastapi_health():
    """Check connectivity and health status of the FastAPI backend service."""
    try:
        res = requests.get(f"{FASTAPI_BASE_URL}/health", timeout=2)
        return jsonify({"fastapi": res.json()})
    except requests.exceptions.RequestException:
        return jsonify({"error": "FastAPI service not reachable"}), 503
