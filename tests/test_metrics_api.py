# tests/test_metrics_api.py
import pytest
from fastapi.testclient import TestClient
from backend.fastapi_app.main import app

client = TestClient(app)

@pytest.mark.metrics
def test_metrics_endpoint_status_code():
    """
    Ensure the /metrics endpoint is reachable and returns 200 OK.
    """
    response = client.get("/metrics/")
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    assert "rl_experiments_active" in response.text, "Missing core metric in response"
    assert "rl_training_completed_total" in response.text, "Missing training metric"
    assert "rl_avg_benchmark_latency_ms" in response.text, "Missing latency metric"

@pytest.mark.metrics
def test_metrics_format_and_content_type():
    """
    Validate that /metrics returns Prometheus format and content type.
    """
    response = client.get("/metrics/")
    content_type = response.headers.get("content-type", "")
    assert response.status_code == 200
    assert "text/plain" in content_type or "prometheus" in content_type

    # Instead of checking the first line, confirm key metrics exist anywhere
    text = response.text
    assert "# HELP rl_experiments_active" in text
    assert "# HELP rl_training_completed_total" in text
    assert "# HELP rl_avg_benchmark_latency_ms" in text


@pytest.mark.metrics
def test_metrics_values_are_numeric():
    """
    Ensure numeric metrics exist and have plausible values.
    """
    response = client.get("/metrics/")
    text = response.text

    def _extract_metric(name):
        for line in text.splitlines():
            if line.startswith(name):
                try:
                    return float(line.split()[-1])
                except Exception:
                    return None
        return None

    exp_active = _extract_metric("rl_experiments_active")
    training_total = _extract_metric("rl_training_completed_total")
    latency_ms = _extract_metric("rl_avg_benchmark_latency_ms")

    assert exp_active is not None and exp_active >= 0
    assert training_total is not None and training_total >= 0
    assert latency_ms is not None and latency_ms > 0

@pytest.mark.metrics
def test_metrics_contains_standard_python_metrics():
    """
    Confirm Python runtime metrics are included in the Prometheus output.
    """
    response = client.get("/metrics/")
    text = response.text
    assert "# HELP python_gc_objects_collected_total" in text
    assert "# HELP process_resident_memory_bytes" in text
    assert "# HELP process_cpu_seconds_total" in text
