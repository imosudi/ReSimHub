## 🧪 Testing

ReSimHub includes a comprehensive testing suite for API validation, benchmark execution, and quality assurance.

### Quick Test Run

```bash
# Install dependencies
pip install -r requirements.txt

# Prepare storage
mkdir -p storage/models

# Run tests
python -m pytest tests/test_benchmark_api.py -v --disable-warnings
```

### Expected Results

```
tests/test_benchmark_api.py::test_upload_model PASSED                    [ 20%]
tests/test_benchmark_api.py::test_run_benchmark PASSED                   [ 40%]
tests/test_benchmark_api.py::test_list_recent_results PASSED             [ 60%]
tests/test_benchmark_api.py::test_compare_models PASSED                  [ 80%]
tests/test_benchmark_api.py::test_invalid_compare_model_id PASSED        [100%]

================================================= 5 passed in 1.33s ==================================================
```

### 📘 Complete Testing Documentation

For detailed setup instructions, configuration options, CI/CD integration, and troubleshooting guides, see:

**→ [Complete Testing Guide](docs/resimhub_test_guide.md)**

