# PyJobber 💼

A modern, multi-threaded job scraping and filtering application that fetches job listings from Romanian job sites, applies intelligent filtering, and provides a real-time dashboard for viewing and exporting results.

## ✨ Features

- 🔄 **Multi-threaded scraping**: Background scraper runs while UI remains responsive
- 🚀 **Instant UI launch**: Dashboard loads immediately with cached data
- 📊 **Real-time status**: See scraper progress, duration, and completion status
- 🔍 **Smart search & filter**: Search jobs by title, company, with real-time results
- ✅ **Job selection & export**: Select jobs with external URLs and export to CSV
- 🔁 **Auto-refresh**: Optional 5-second auto-refresh to see new data
- 🎯 **Multi-platform scraping**: Fetches jobs from multiple job providers
- ⏱️ **Rate limiting**: Prevents API abuse with 24-hour intervals
- 🛡️ **Smart filtering**: Removes unwanted jobs based on configurable banned words
- 💾 **Intelligent caching**: Stores results locally to avoid unnecessary API calls
- 🎨 **Enhanced UI**: Beautiful Streamlit interface with icons, metrics, and tabs
- 🏗️ **Modular architecture**: Clean, maintainable codebase with proper separation of concerns
- 🧪 **Comprehensive tests**: 55+ tests with 22% coverage

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd PyJobber

# Install dependencies
pip install -e .
# OR using uv
uv sync
```

### Usage

#### Recommended: Multi-Threaded Mode (Default)

```bash
# Start with background scraping + UI (RECOMMENDED)
streamlit run main.py
```

This will:
1. Check if 24 hours have passed since last scrape
2. Start background scraper thread if needed
3. Launch Streamlit UI immediately with cached data
4. Display scraper status in real-time
5. Update data when scraping completes

#### Other Modes

```bash
# Run only the scraper (no UI)
python main.py --scrape

# Force re-scrape (removes 24-hour rate limit)
python main.py --force
# Then run: streamlit run main.py

# Disable background scraping
python main.py --streamlit --no-background

# Get help
python main.py --help
```

### UI Features

Once the dashboard is running, you can:

- 📊 **View Summary Statistics** - See job counts at a glance
- 🔍 **Search Jobs** - Filter by title or company name
- ✅ **Select Jobs** - Use checkboxes to select jobs with external URLs
- 📥 **Export Selected** - Save to `data/selected/selected_jobs_export.csv`
- 🔄 **Monitor Scraper** - See real-time scraping progress
- 🔁 **Auto-Refresh** - Enable 5-second auto-refresh to see new data

## 📁 Project Structure

```
PyJobber/
├── src/pyjobber/              # Main package
│   ├── core/                  # Core business logic
│   │   ├── scraper.py         # Main orchestration
│   │   ├── filters.py         # Job filtering logic
│   │   └── background_scraper.py  # Multi-threading support ⭐
│   ├── providers/             # API integrations
│   │   ├── base.py            # Base provider interface
│   │   ├── bestjobs.py        # Provider A integration
│   │   └── ejobs.py           # Provider B integration
│   ├── storage/               # Data persistence
│   │   └── csv_handler.py     # CSV operations
│   ├── ui/                    # User interfaces
│   │   └── streamlit_app.py   # Web dashboard ⭐
│   └── utils/                 # Utilities
│       └── rate_limiter.py    # Rate limiting logic
├── tests/                     # Test suite ⭐
│   ├── conftest.py            # Shared fixtures
│   ├── core/                  # Core tests (17 tests)
│   ├── storage/               # Storage tests (20 tests)
│   └── utils/                 # Utility tests (18 tests)
├── docs/                      # Documentation
│   └── MULTI_THREADING.md     # Multi-threading guide ⭐
├── data/                      # Data and configuration
│   ├── banned_words.txt       # Words to filter out
│   ├── cache/                 # Cached job data
│   └── selected/              # Exported selections ⭐
├── main.py                    # CLI entry point ⭐
├── pytest.ini                 # Pytest configuration ⭐
└── pyproject.toml             # Dependencies
```

**⭐ = New in v0.2.0**

## 🔄 How It Works

### Multi-Threading Flow

```
User starts app → Check 24h rate limit → Start background scraper (if needed)
                                       ↓
                        Launch UI immediately with cached data
                                       ↓
           Scraper runs in background | User interacts with UI
                                       ↓
                      Scraping completes → User refreshes to see new data
```

### Core Features

#### 1. Rate-Limited Scraping
PyJobber uses intelligent rate limiting to respect API limits:
- Checks timestamp of last successful run
- Only fetches new data if 24+ hours have passed
- Uses cached data when available
- Prevents unnecessary API calls

#### 2. Multi-Provider Architecture
Modular design supports multiple job sites:
- **Provider A**: Primary job board integration
- **Provider B**: Secondary job board integration
- **Extensible**: Easy to add new providers

#### 3. Smart Filtering System
- Loads banned words from configurable text file
- Filters job titles containing unwanted terms
- Maintains original data for reference
- Tracks filtering statistics

#### 4. Data Processing Pipeline
```
API Fetch → Data Validation → Word Filtering → Link Generation → CSV Export → Dashboard
```

## Configuration

### Banned Words Filter

Edit `data/banned_words.txt` to customize job filtering:

```text
sales
marketing
manager
consultant
```

Each line represents a word/phrase to filter out from job titles (case-insensitive).

### Cache Directory

Job data is cached in `data/cache/`:
- `bjobs.csv` - Provider A listings
- `ejobs.csv` - Provider B listings
- `externalJobs.csv` - Jobs with external application URLs

### Selected Jobs Export

Selected jobs are exported to `data/selected/`:
- `selected_jobs_export.csv` - User-selected jobs with external URLs

## API Documentation

### Core Classes

#### `JobProvider` (Base Class)
Abstract base class for all job providers.

**Methods:**
- `fetch_jobs()` → `List[Dict]` - Fetch jobs from provider
- `get_required_columns()` → `List[str]` - Get required data columns
- `create_job_link(job_data)` → `str` - Generate direct job link

### Core Functions

#### Scraping
```python
from src.pyjobber.core.scraper import run_scraper_or_load_cache

# Main entry point - handles rate limiting and caching
df_jobs_a, df_jobs_b, external_jobs = run_scraper_or_load_cache()
```

#### Background Scraping
```python
from src.pyjobber.core.background_scraper import start_background_scraper

# Start background scraper
scraper = start_background_scraper()

# Check status
status_info = scraper.get_status_info()
print(f"Status: {status_info['status']}")
```

#### Filtering
```python
from src.pyjobber.core.filters import filter_jobs_by_banned_words

# Filter DataFrame by banned words
filtered_df = filter_jobs_by_banned_words(df, "data/banned_words.txt")
```

#### Storage
```python
from src.pyjobber.storage.csv_handler import save_jobs_to_csv, load_jobs_from_csv

# Save job data
save_jobs_to_csv(df_jobs_a, df_jobs_b, external_jobs)

# Load cached data
df_jobs_a, df_jobs_b, external_jobs = load_jobs_from_csv()
```

## Development

### Adding New Job Providers

1. Create a new provider class inheriting from `JobProvider`:

```python
# src/pyjobber/providers/newprovider.py
from .base import JobProvider

class NewProvider(JobProvider):
    def fetch_jobs(self):
        # Implement API fetching logic
        pass

    def get_required_columns(self):
        return ['id', 'title', 'company']

    def create_job_link(self, job_data):
        return f"https://jobsite.com/jobs/{job_data['id']}"
```

2. Integration in scraper:

```python
# src/pyjobber/core/scraper.py
from ..providers.newprovider import NewProvider

def scrape_jobs():
    provider = NewProvider()
    data = provider.fetch_jobs()
    # ... process data
```

### Testing

PyJobber includes a comprehensive test suite with 55+ tests covering core functionality.

#### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run all tests
pytest tests/

# Run with coverage report
pytest tests/ --cov=src/pyjobber --cov-report=term-missing --cov-report=html

# Run specific test file
pytest tests/core/test_filters.py -v
```

#### Test Coverage

**Current Coverage: 22% (Phase 1 Complete)**

| Module | Coverage | Tests | Status |
|--------|----------|-------|--------|
| `filters.py` | 90% | 17 tests | ✅ |
| `csv_handler.py` | 100% | 20 tests | ✅ |
| `rate_limiter.py` | 100% | 18 tests | ✅ |

See [`tests/README.md`](tests/README.md) for detailed testing documentation.

#### Quick Validation

```bash
# Test imports
python -c "from src.pyjobber.core.scraper import run_scraper_or_load_cache; print('✅ Imports work')"

# Test multi-threading
python -c "from src.pyjobber.core.background_scraper import BackgroundScraper; print('✅ Multi-threading works')"
```

## Troubleshooting

### Common Issues

**"No module named 'streamlit'"**
- Solution: Install dependencies with `pip install -e .`

**"CSV files not found"**
- Solution: Run the scraper first: `python main.py --scrape`

**"Script last ran X hours ago"**
- This is normal rate limiting behavior
- Wait for 24-hour interval or use `python main.py --force` for testing

**SSL/urllib3 warnings**
- These are harmless warnings about OpenSSL versions
- Functionality is not affected

**UI shows old data after scraping completes**
- Solution: Click "🔄 Refresh Now" or enable auto-refresh

**Export fails with "directory not found"**
- Solution: Directory is created automatically, but you can create manually:
  ```bash
  mkdir -p data/selected
  ```

### Debug Mode

Enable verbose logging by modifying the logging level in provider files.

## Contributing

1. Follow the existing code structure and patterns
2. Add type hints to all functions
3. Include error handling and logging
4. Update documentation for new features
5. Write tests for new functionality
6. Run test suite before submitting PRs: `pytest tests/`

## Documentation

- [`docs/MULTI_THREADING.md`](docs/MULTI_THREADING.md) - Multi-threading architecture and usage
- [`tests/README.md`](tests/README.md) - Testing guide and best practices
- [`CHANGES.md`](CHANGES.md) - Version history and changelog


---

**Made with ❤️ for job seekers**
