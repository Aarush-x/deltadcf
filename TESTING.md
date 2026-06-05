# Testing Philosophy

100% test coverage is the key to great vibe coding. Tests let you move fast, trust your instincts, and ship with confidence — without them, vibe coding is just yolo coding. With tests, it's a superpower.

## Framework
This project uses **pytest** with **pytest-cov** for testing and coverage tracking.

## Running Tests
To run the full test suite with coverage report:
```bash
source venv/bin/activate
pytest
```

## Test Layers
- **Unit Tests (`tests/test_*.py`)**: Tests individual components like the `DCFEngine` and `ResearchChecklist` in isolation.
- **Integration Tests**: Tests the interaction between the `FinancialDataFetcher` and external APIs (using mocks).

## Conventions
- **File Naming**: Test files must start with `test_` and reside in the `tests/` directory.
- **Mocking**: Use `pytest-mock` or `unittest.mock` to stub external network calls (yfinance, SEC, BSE/NSE).
- **Assertions**: Use clear, descriptive assertions that test real behavior, not just existence.
