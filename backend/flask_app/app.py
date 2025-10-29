from flask import Flask, jsonify
import requests

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
