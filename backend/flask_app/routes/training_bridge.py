# backend/flask_app/routes/training_bridge.py
from flask import Blueprint, request, jsonify
import asyncio
from flask_app.services.api_proxy import FastAPIProxy

bridge_bp = Blueprint("bridge", __name__, url_prefix="/api/v1")


@bridge_bp.route("/start_training", methods=["POST"])
def start_training():
    """
    Proxy endpoint to FastAPI /orchestrate/train
    """
    payload = request.json
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(FastAPIProxy.post_train(payload))
    return jsonify(result)


@bridge_bp.route("/task_status/<task_id>", methods=["GET"])
def task_status(task_id):
    """
    Proxy endpoint to fetch task status from FastAPI
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(FastAPIProxy.get_task_status(task_id))
    return jsonify(result)


@bridge_bp.route("/analytics/experiment/<int:experiment_id>", methods=["GET"])
def experiment_analytics(experiment_id):
    """
    Proxy endpoint to fetch analytics for a specific experiment
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(FastAPIProxy.get_experiment_analytics(experiment_id))
    return jsonify(result)


@bridge_bp.route("/analytics/recent", methods=["GET"])
def recent_analytics():
    """
    Proxy endpoint to fetch recent experiment analytics
    """
    limit = int(request.args.get("limit", 5))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(FastAPIProxy.get_recent_analytics(limit))
    return jsonify(result)


