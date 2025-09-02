# PyJobber Development Changes

This document outlines the key improvements made to the PyJobber project and suggests areas for further learning.

## Major Changes Made

### 1. Enhanced Error Handling & Logging
- **Added comprehensive try-catch blocks** throughout the API request functions
- **Implemented detailed logging** with structured messages (`[INFO]`, `[ERROR]`, `[SUCCESS]`)
- **Added network timeouts** (30 seconds) to prevent hanging requests
- **Added HTTP status validation** using `response.raise_for_status()`
- **Graceful degradation** for API structure changes (missing keys, pagination issues)

### 2. Rate Limiting Improvements
- **Fixed timestamp updating logic** - only updates on successful completion
- **Allows immediate retries** when scraping fails (timestamp not updated on failure)
- **Better error reporting** for timestamp file issues

### 3. Command Line Interface (CLI)
- **Added argparse support** for command-line options
- **Implemented `--scrape` flag** for explicit scraping mode
- **Implemented `--streamlit` flag** for dashboard mode
- **Default behavior** runs scraping when no flags provided

### 4. Streamlit Dashboard Integration
- **Created web-based data visualization** using Streamlit
- **Organized data in tabs** (BestJobs, eJobs, External Jobs)
- **Added job count summaries** and data overview
- **Proper error handling** for missing CSV files
- **Responsive design** with container-width tables

### 5. Code Quality Improvements
- **Fixed type annotations** with proper return types (`Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]`)
- **Resolved linting issues** (removed f-strings without placeholders, unused imports)
- **Added proper imports** for typing support
- **Improved code structure** with better separation of concerns

### 6. Dependency Management
- **Downgraded urllib3** to fix SSL compatibility issues with LibreSSL
- **Added proper version constraints** in pyproject.toml

## Learning Areas

### 1. Error Handling Patterns
**Study Topics:**
- Python exception hierarchies (`requests.exceptions.RequestException`, `KeyError`, etc.)
- Try-catch-finally blocks and when to use each
- Logging best practices with different log levels
- Defensive programming techniques
- Circuit breaker patterns for API failures

**Example Code to Study:**
```python
try:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    if 'expected_key' not in data:
        raise KeyError("Missing expected key in API response")
except requests.exceptions.RequestException as e:
    logger.error(f"Network error: {e}")
except KeyError as e:
    logger.error(f"Data structure error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

### 2. API Integration Best Practices
**Study Topics:**
- HTTP status codes and error handling
- Rate limiting and backoff strategies
- API pagination patterns
- Request timeouts and retries
- API response validation
- JSON parsing safety

### 3. Command Line Interface (CLI) Development
**Study Topics:**
- `argparse` module for argument parsing
- Subcommands and argument groups
- Help text and documentation
- Environment variable integration
- Configuration file parsing

### 4. Web Dashboard Development with Streamlit
**Study Topics:**
- Streamlit component library
- Session state management
- Data visualization with pandas/plotly
- Layout and UI design patterns
- Caching strategies for performance
- Deployment options

### 5. Data Processing & Validation
**Study Topics:**
- Pandas DataFrame operations
- Data cleaning and normalization
- Type validation and conversion
- CSV file handling best practices
- Data pipeline architecture

### 6. Type Annotations & Static Analysis
**Study Topics:**
- Python typing module (`Optional`, `Tuple`, `List`, etc.)
- Type hints for functions and variables
- Static analysis tools (Pylance, mypy)
- Generic types and protocols

## Recommended Next Steps

1. **Study the error handling patterns** in `jobs.py` - understand how different exception types are caught and handled
2. **Experiment with the CLI** - try different argument combinations and see how argparse works
3. **Explore Streamlit documentation** - learn about different components and layouts
4. **Practice API debugging** - use tools like curl or Postman to test the APIs manually
5. **Learn about logging frameworks** - consider upgrading to Python's `logging` module for production use

## Files Modified

- `lib/linkProvider/jobs.py` - Enhanced with comprehensive error handling and logging
- `lib/linkProvider/linkProvider.py` - Improved rate limiting and timestamp management
- `main.py` - Complete rewrite with CLI and Streamlit integration
- `pyproject.toml` - Updated dependencies (urllib3 downgrade)
- `CLAUDE.md` - Updated documentation with new commands and features