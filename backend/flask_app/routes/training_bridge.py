# backend/flask_app/routes/training_bridge.py
from flask import Blueprint, request, jsonify
import asyncio
import httpx
try:
    from backend.flask_app.services.api_proxy import FastAPIProxy
except ImportError:
    from flask_app.services.api_proxy import FastAPIProxy

bridge_bp = Blueprint("bridge", __name__, url_prefix="/api/v1")

def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def handle_proxy_call(coro):
    try:
        return jsonify(run_async(coro))
    except httpx.HTTPStatusError as exc:
        try:
            return jsonify(exc.response.json()), exc.response.status_code
        except Exception:
            return jsonify({"error": f"Backend returned error code {exc.response.status_code}"}), exc.response.status_code
    except Exception as exc:
        return jsonify({"error": f"Failed to connect to FastAPI backend: {str(exc)}"}), 503

@bridge_bp.route("/start_training", methods=["POST"])
def start_training():
    return handle_proxy_call(FastAPIProxy.post_train(request.json))

@bridge_bp.route("/task_status/<task_id>", methods=["GET"])
def task_status(task_id):
    return handle_proxy_call(FastAPIProxy.get_task_status(task_id))

@bridge_bp.route("/analytics/experiment/<int:experiment_id>", methods=["GET"])
def experiment_analytics(experiment_id):
    return handle_proxy_call(FastAPIProxy.get_experiment_analytics(experiment_id))

@bridge_bp.route("/analytics/recent", methods=["GET"])
def recent_analytics():
    limit = int(request.args.get("limit", 5))
    return handle_proxy_call(FastAPIProxy.get_recent_analytics(limit))

@bridge_bp.route("/environments", methods=["GET", "POST"])
def manage_environments():
    if request.method == "POST":
        return handle_proxy_call(FastAPIProxy.post_environment(request.json))
    return handle_proxy_call(FastAPIProxy.get_environments())

@bridge_bp.route("/experiments", methods=["GET", "POST"])
def manage_experiments():
    if request.method == "POST":
        return handle_proxy_call(FastAPIProxy.post_experiment(request.json))
    return handle_proxy_call(FastAPIProxy.get_experiments())

@bridge_bp.route("/benchmark/upload", methods=["POST"])
def benchmark_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400
    
    # Forward multipart file
    files = {"file": (file.filename, file.read(), file.content_type)}
    return handle_proxy_call(FastAPIProxy.post_benchmark_upload(files))

@bridge_bp.route("/benchmark/run", methods=["POST"])
def benchmark_run():
    # Frontend sends JSON or form data, FastAPI expects Form data.
    # Convert incoming JSON/Form parameters to simple dict of strings
    payload = request.json or request.form.to_dict()
    return handle_proxy_call(FastAPIProxy.post_benchmark_run(payload))

@bridge_bp.route("/benchmark/recent", methods=["GET"])
def benchmark_recent():
    limit = int(request.args.get("limit", 10))
    return handle_proxy_call(FastAPIProxy.get_benchmark_recent(limit))

@bridge_bp.route("/benchmark/compare", methods=["GET"])
def benchmark_compare():
    model_ids = request.args.get("model_ids", "")
    env = request.args.get("env", None)
    return handle_proxy_call(FastAPIProxy.get_benchmark_compare(model_ids, env))

@bridge_bp.route("/schedule_batch", methods=["POST"])
def schedule_batch():
    return handle_proxy_call(FastAPIProxy.post_schedule_batch(request.json or {}))

@bridge_bp.route("/batches/<batch_id>", methods=["GET"])
def get_batch(batch_id):
    return handle_proxy_call(FastAPIProxy.get_batch_status(batch_id))

@bridge_bp.route("/batches", methods=["GET"])
def list_batches():
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    return handle_proxy_call(FastAPIProxy.get_batches(limit, offset))

@bridge_bp.route("/checkpoints", methods=["GET"])
def list_checkpoints():
    task_id = request.args.get("task_id")
    algo = request.args.get("algo")
    is_best_raw = request.args.get("is_best")
    is_best = is_best_raw.lower() == "true" if is_best_raw is not None else None
    limit = int(request.args.get("limit", 20))
    offset = int(request.args.get("offset", 0))
    return handle_proxy_call(FastAPIProxy.get_checkpoints(task_id, algo, is_best, limit, offset))

@bridge_bp.route("/checkpoints/best", methods=["GET"])
def best_checkpoint():
    task_id = request.args.get("task_id")
    algo = request.args.get("algo")
    env_name = request.args.get("env_name")
    return handle_proxy_call(FastAPIProxy.get_best_checkpoint(task_id, algo, env_name))

@bridge_bp.route("/checkpoints/<checkpoint_id>", methods=["GET"])
def checkpoint_detail(checkpoint_id):
    return handle_proxy_call(FastAPIProxy.get_checkpoint_by_id(checkpoint_id))

@bridge_bp.route("/checkpoints/<checkpoint_id>/resume", methods=["POST"])
def resume_training(checkpoint_id):
    return handle_proxy_call(FastAPIProxy.post_resume_checkpoint(checkpoint_id, request.json or {}))

@bridge_bp.route("/simulator/health", methods=["GET"])
def simulator_health():
    return handle_proxy_call(FastAPIProxy.get_simulator_health())

@bridge_bp.route("/simulator/environments", methods=["GET"])
def simulator_environments():
    return handle_proxy_call(FastAPIProxy.get_simulator_environments())

@bridge_bp.route("/simulator/reset", methods=["POST"])
def simulator_reset():
    return handle_proxy_call(FastAPIProxy.post_simulator_reset(request.json or {}))

@bridge_bp.route("/simulator/step", methods=["POST"])
def simulator_step():
    return handle_proxy_call(FastAPIProxy.post_simulator_step(request.json or {}))

@bridge_bp.route("/simulator/batch_step", methods=["POST"])
def simulator_batch_step():
    return handle_proxy_call(FastAPIProxy.post_simulator_batch_step(request.json or {}))

@bridge_bp.route("/simulator/stream", methods=["POST"])
def simulator_stream():
    return handle_proxy_call(FastAPIProxy.post_simulator_stream(request.json or {}))

@bridge_bp.route("/simulator/benchmark", methods=["POST"])
def simulator_benchmark():
    return handle_proxy_call(FastAPIProxy.post_simulator_benchmark(request.json or {}))



