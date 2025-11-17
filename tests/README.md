# PyJobber Test Suite

This directory contains the test suite for PyJobber. The tests are organized by module and use pytest as the testing framework.

## Current Test Coverage: 22%

### Phase 1 (Completed) - Critical Business Logic
- `core/test_filters.py` - **90% coverage** - Job filtering logic
- `storage/test_csv_handler.py` - **100% coverage** - CSV operations
- `utils/test_rate_limiter.py` - **100% coverage** - Rate limiting

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures for all tests
├── README.md                # This file
├── core/                    # Core business logic tests
│   ├── test_filters.py      # Job filtering tests (17 tests)
│   └── test_scraper.py      # TODO: Scraper integration tests
├── providers/               # Provider implementation tests
│   ├── test_bestjobs.py     # TODO: BestJobs API tests
│   └── test_ejobs.py        # TODO: eJobs API tests
├── storage/                 # Data persistence tests
│   └── test_csv_handler.py  # CSV operations tests (20 tests)
└── utils/                   # Utility function tests
    └── test_rate_limiter.py # Rate limiter tests (18 tests)
```

## Running Tests

### Install Test Dependencies

```bash
# Using uv (recommended)
uv sync --extra test

# Or using pip
pip install -e ".[test]"
```

### Run All Tests

```bash
# Basic test run
pytest tests/

# Verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src/pyjobber --cov-report=term-missing --cov-report=html
```

### Run Specific Test Files

```bash
# Run only filter tests
pytest tests/core/test_filters.py

# Run only CSV handler tests
pytest tests/storage/test_csv_handler.py

# Run only rate limiter tests
pytest tests/utils/test_rate_limiter.py
```

### Run Specific Test Classes or Functions

```bash
# Run a specific test class
pytest tests/core/test_filters.py::TestLoadBannedWords

# Run a specific test function
pytest tests/core/test_filters.py::TestLoadBannedWords::test_load_banned_words_success
```

### Coverage Reports

Generate an HTML coverage report:

```bash
pytest tests/ --cov=src/pyjobber --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view detailed coverage information.

## Test Categories

### Unit Tests

Tests for individual functions in isolation:
- `test_filters.py` - Filter logic, banned word loading
- `test_rate_limiter.py` - Timestamp checking and updating
- `test_csv_handler.py` - CSV save and load operations

### Integration Tests

Tests that verify multiple components working together:
- `test_csv_handler.py::TestCSVHandlerIntegration` - Save/load roundtrip
- `test_rate_limiter.py::TestRateLimiterIntegration` - Full workflow

## What's Tested

### Core Filtering (`test_filters.py`)
- ✅ Loading banned words from file
- ✅ Filtering jobs by banned words (case-insensitive)
- ✅ Partial word matching
- ✅ Empty DataFrames and files
- ✅ Special characters in banned words
- ✅ Multiple banned words in titles
- ✅ DataFrame structure preservation

### CSV Storage (`test_csv_handler.py`)
- ✅ Creating cache directories
- ✅ Saving and loading DataFrames
- ✅ Handling external jobs
- ✅ Missing files and directories
- ✅ Empty DataFrames
- ✅ File overwriting
- ✅ Complete save/load roundtrip

### Rate Limiting (`test_rate_limiter.py`)
- ✅ Timestamp file creation and updates
- ✅ 24-hour interval checking
- ✅ Edge cases (exactly 24 hours, future timestamps)
- ✅ Corrupted and missing files
- ✅ File permission errors (when not running as root)
- ✅ ISO format timestamp validation
- ✅ Full rate limiter workflow

## What Still Needs Testing

### Phase 2 - Provider Testing (Priority: High)
- [ ] `test_bestjobs.py` - BestJobs API integration
  - Mock API responses
  - Network error handling
  - Malformed response handling
  - Link generation

- [ ] `test_ejobs.py` - eJobs API integration
  - Multi-page fetching
  - Pagination logic
  - Network error handling
  - Link generation

### Phase 3 - Integration Tests (Priority: Medium)
- [ ] `test_scraper.py` - End-to-end scraping workflow
  - Scraper orchestration
  - Provider integration
  - Error handling
  - Data transformation

- [ ] `test_main.py` - CLI entry point
  - Command-line argument handling
  - Exit codes
  - Flag combinations

## Fixtures

The `conftest.py` file provides shared fixtures for all tests:

- `temp_cache_dir` - Temporary cache directory
- `temp_data_dir` - Temporary data directory
- `banned_words_file` - Sample banned words file
- `empty_banned_words_file` - Empty banned words file
- `sample_bjobs_data` - Sample BestJobs data
- `sample_ejobs_data` - Sample eJobs data
- `sample_bjobs_df` - Sample BestJobs DataFrame
- `sample_ejobs_df` - Sample eJobs DataFrame
- `timestamp_file` - Temporary timestamp file
- `old_timestamp_file` - Timestamp > 24 hours old
- `recent_timestamp_file` - Timestamp < 24 hours old
- `corrupted_timestamp_file` - Invalid timestamp data

## Writing New Tests

### Test Naming Conventions

- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test functions: `test_<function_description>`

### Example Test Structure

```python
"""Tests for module functionality."""
import pytest
from src.pyjobber.module import function_to_test


class TestFunctionName:
    """Tests for function_to_test."""

    def test_basic_functionality(self):
        """Test basic use case."""
        result = function_to_test("input")
        assert result == "expected"

    def test_error_handling(self):
        """Test error conditions."""
        with pytest.raises(ValueError):
            function_to_test("invalid")

    def test_with_fixture(self, temp_cache_dir):
        """Test using a fixture."""
        result = function_to_test(temp_cache_dir)
        assert result is not None
```

### Using Fixtures

```python
def test_with_multiple_fixtures(self, sample_bjobs_df, banned_words_file):
    """Test using multiple fixtures."""
    # Fixtures are automatically provided by pytest
    result = filter_jobs_by_banned_words(sample_bjobs_df, banned_words_file)
    assert len(result) > 0
```

## Continuous Integration

To set up CI testing with GitHub Actions, create `.github/workflows/test.yml`:

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -e ".[test]"
      - name: Run tests
        run: |
          pytest tests/ --cov=src/pyjobber --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

## Test Coverage Goals

- **Phase 1 (Current):** 22% - Core business logic tested
- **Phase 2 Target:** 70-80% - Add provider tests
- **Phase 3 Target:** 85-90% - Add integration tests

## Best Practices

1. **Test one thing per test** - Each test should verify a single behavior
2. **Use descriptive names** - Test names should describe what they're testing
3. **Arrange-Act-Assert** - Structure tests with clear setup, execution, and verification
4. **Use fixtures** - Avoid duplicating test setup code
5. **Test edge cases** - Empty inputs, None values, error conditions
6. **Mock external dependencies** - Use `responses` or `pytest-mock` for API calls
7. **Keep tests fast** - Unit tests should run in milliseconds

## Troubleshooting

### Tests fail with import errors
- Make sure you've installed test dependencies: `pip install -e ".[test]"`
- Ensure you're in the project root directory

### Coverage report not generating
- Install coverage: `pip install pytest-cov`
- Check that you're using the correct source path: `--cov=src/pyjobber`

### Tests pass locally but fail in CI
- Check Python version compatibility
- Ensure all test dependencies are in `pyproject.toml`
- Look for environment-specific assumptions (file paths, permissions)

## Contributing

When adding new functionality to PyJobber:

1. Write tests for the new code **before** or alongside implementation
2. Aim for at least 80% coverage of new code
3. Include both success and error cases
4. Update this README if adding new test files or categories
5. Run the full test suite before submitting PRs: `pytest tests/`

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Coverage.py](https://coverage.readthedocs.io/)
- [Testing Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
