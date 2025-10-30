# Quick Start

### 1. Clone & Setup
```bash
# Clone repository
git clone https://github.com/imosudi/ReSimHub
cd ReSimHub

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**Manual installation** (if requirements.txt unavailable):
```bash
pip install fastapi uvicorn pytest pytest-cov requests pydantic redis pandas numpy httpx
```

### 3. Prepare Storage
```bash
mkdir -p storage/models
mkdir -p storage/benchmarks
mkdir -p logs
```

---

## Running Tests

### Basic Test Execution
```bash
# Run all tests with verbose output
python -m pytest tests/test_benchmark_api.py -v --disable-warnings

# Run with coverage report
python -m pytest tests/test_benchmark_api.py -v --cov=app --cov-report=html

# Run specific test
python -m pytest tests/test_benchmark_api.py::test_upload_model -v
```

### Advanced Options
```bash
# Run tests in parallel (faster)
pytest tests/ -n auto

# Run with detailed output
pytest tests/ -vv -s

# Generate JUnit XML report (for CI/CD)
pytest tests/ --junitxml=reports/junit.xml

# Run tests matching pattern
pytest tests/ -k "benchmark" -v
```

---

## Expected Test Results

| Test Name | Expected Outcome | Validation Points |
|-----------|------------------|-------------------|
| `test_upload_model` | ✅ Model uploads successfully | • `model_id` returned<br>• `status: "uploaded"`<br>• File stored in `/storage/models/` |
| `test_run_benchmark` | ✅ Benchmark executes | • `mean_reward` (float)<br>• `std_reward` (float)<br>• `status: "completed"`<br>• Execution time logged |
| `test_list_recent_results` | ✅ Recent results listed | • Response count ≥ 1<br>• Valid list structure<br>• Sorted by timestamp (desc) |
| `test_compare_models` | ✅ Models compared | • Sorted by `mean_reward`<br>• All model_ids present<br>• Comparative metrics included |
| `test_invalid_compare_model_id` | ✅ Error handling works | • Returns error JSON<br>• No exceptions raised<br>• Appropriate HTTP status |

---

## Example Output

### Successful Test Run
```
======================================================= test session starts =======================================================
platform linux -- Python 3.12.3, pytest-8.4.2, pluggy-1.6.0
rootdir: /path/to/ReSimHub
plugins: cov-5.0.0, asyncio-0.23.0
collected 5 items

tests/test_benchmark_api.py::test_upload_model PASSED                                                                      [ 20%]
tests/test_benchmark_api.py::test_run_benchmark PASSED                                                                     [ 40%]
tests/test_benchmark_api.py::test_list_recent_results PASSED                                                               [ 60%]
tests/test_benchmark_api.py::test_compare_models PASSED                                                                    [ 80%]
tests/test_benchmark_api.py::test_invalid_compare_model_id PASSED                                                         [100%]

================================================= 5 passed, 42 warnings in 1.33s ==================================================
```

### Understanding Warnings
Most warnings are non-critical:
- **Redis connection warnings**: Normal when Redis is unavailable (fallback to local storage)
- **DeprecationWarnings**: Library-related, won't affect functionality
- **PytestUnknownMarkWarning**: Can be suppressed in `pytest.ini`

---

## 🔍 Post-Test Verification

### 1. Check Test Artifacts
```bash
# View generated model files
ls -lh storage/models/

# View benchmark results
ls -lh storage/benchmarks/

# Check logs
tail -n 50 logs/benchmark.log
```

### 2. Manual API Testing
```bash
# Start the server
uvicorn app.main:app --reload --port 8000

# In another terminal, test endpoints
curl -X POST "http://localhost:8000/benchmark/upload" \
  -F "file=@test_model.pkl"

curl "http://localhost:8000/benchmark/recent?limit=10"
```

### 3. Cleanup
```bash
# Remove test files
rm -rf storage/models/*
rm -rf storage/benchmarks/*

# Or use cleanup script
python scripts/cleanup_test_data.py
```

---

## Configuration Files

### pytest.ini
Create in project root to suppress warnings:
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --disable-warnings
    --tb=short
    --cov=app
    --cov-report=term-missing
    --cov-report=html
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

### .coveragerc
For coverage configuration:
```ini
[run]
source = app
omit = 
    */tests/*
    */venv/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## CI/CD Integration

### GitHub Actions Example
Create `.github/workflows/test.yml`:
```yaml
name: ReSimHub Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Prepare storage
      run: mkdir -p storage/models storage/benchmarks
    
    - name: Run tests
      run: pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Troubleshooting

### Issue: Tests Fail with Import Errors
```bash
# Ensure you're in virtual environment
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Storage Permission Denied
```bash
# Fix permissions
chmod -R 755 storage/
```

### Issue: Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Issue: Redis Connection Warnings
These are typically harmless. To suppress:
```python
# In tests/conftest.py
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
```

---

## Performance Benchmarking

### Test Execution Time
```bash
# Profile test execution
pytest tests/ --durations=10

# Run with timing
pytest tests/ -v --benchmark-only
```

### Expected Performance
- **test_upload_model**: < 0.1s
- **test_run_benchmark**: 0.5-1.0s (includes simulation)
- **test_list_recent_results**: < 0.05s
- **test_compare_models**: < 0.1s
- **test_invalid_compare_model_id**: < 0.05s

**Total Suite**: Should complete in < 2 seconds

---

## Best Practices

1. **Run tests before commits**
   ```bash
   pytest tests/ -v && git commit
   ```

2. **Keep test data isolated**
   - Use separate directories for test artifacts
   - Clean up after tests with fixtures

3. **Mock external dependencies**
   - Use `unittest.mock` for Redis, file systems
   - Keep tests fast and deterministic

4. **Test edge cases**
   - Empty files
   - Corrupted models
   - Concurrent requests

5. **Document test scenarios**
   - Add docstrings to test functions
   - Explain complex assertions

---

## Additional Resources

- **FastAPI Testing**: https://fastapi.tiangolo.com/tutorial/testing/
- **Pytest Documentation**: https://docs.pytest.org/
- **Coverage.py Guide**: https://coverage.readthedocs.io/

---

## License & Attribution

**ReSimHub** — BSD 3-Clause License  
**Author**: Mosudi Isiaka  
**Repository**: [github.com/imosudi/ReSimHub](https://github.com/imosudi/ReSimHub)

---

*"Testing ensures reproducibility — ReSimHub ensures scalability."* 🧩

**Status**: ✅ Production Ready  
**Last Updated**: 2025-10-30
