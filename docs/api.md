# API Documentation

This document provides detailed API documentation for PyJobber's core modules.

## Table of Contents

- [Core Module](#core-module)
- [Providers Module](#providers-module)
- [Storage Module](#storage-module)
- [Utils Module](#utils-module)
- [UI Module](#ui-module)

## Core Module

### `pyjobber.core.scraper`

The main orchestration module for job scraping operations.

#### Functions

##### `scrape_jobs() -> Tuple[pd.DataFrame, pd.DataFrame, Optional[pd.DataFrame]]`

Performs the complete job scraping workflow from multiple providers.

**Returns:**
- `Tuple` containing:
  - `pd.DataFrame`: BestJobs data with columns `['title', 'companyName', 'ownApplyUrl', 'link']`
  - `pd.DataFrame`: eJobs data with columns `['title', 'creationDate', 'expirationDate', 'ownApplyUrl', 'link']`
  - `Optional[pd.DataFrame]`: External jobs data or `None`

**Raises:**
- `Exception`: On API failures or data processing errors

**Example:**
```python
from src.pyjobber.core.scraper import scrape_jobs

try:
    bjobs, ejobs, external = scrape_jobs()
    print(f"Found {len(bjobs)} BestJobs and {len(ejobs)} eJobs")
except Exception as e:
    print(f"Scraping failed: {e}")
```

##### `run_scraper_or_load_cache() -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]`

Main entry point that handles rate limiting and caching logic.

**Returns:**
- `Tuple` containing DataFrames or `None` values on failure

**Behavior:**
- Checks if 24+ hours have passed since last run
- If yes: runs fresh scraping and updates cache
- If no: loads data from cached CSV files
- Returns `(None, None, None)` on failure

**Example:**
```python
from src.pyjobber.core.scraper import run_scraper_or_load_cache

bjobs, ejobs, external = run_scraper_or_load_cache()
if bjobs is not None:
    print("Data loaded successfully")
else:
    print("Failed to load or scrape data")
```

### `pyjobber.core.filters`

Job filtering and data cleaning utilities.

#### Functions

##### `load_banned_words(banned_words_file: str = "data/banned_words.txt") -> List[str]`

Loads banned words from a text file.

**Parameters:**
- `banned_words_file` (str): Path to banned words file

**Returns:**
- `List[str]`: List of banned words/phrases

**Example:**
```python
from src.pyjobber.core.filters import load_banned_words

banned = load_banned_words("data/banned_words.txt")
print(f"Loaded {len(banned)} banned words")
```

##### `filter_jobs_by_banned_words(df: pd.DataFrame, banned_words_file: str = "data/banned_words.txt") -> pd.DataFrame`

Filters job DataFrame by removing entries with banned words in titles.

**Parameters:**
- `df` (pd.DataFrame): Input DataFrame with 'title' column
- `banned_words_file` (str): Path to banned words file

**Returns:**
- `pd.DataFrame`: Filtered DataFrame

**Example:**
```python
from src.pyjobber.core.filters import filter_jobs_by_banned_words

filtered_jobs = filter_jobs_by_banned_words(jobs_df)
print(f"Filtered out {len(jobs_df) - len(filtered_jobs)} jobs")
```

## Providers Module

### `pyjobber.providers.base`

Abstract base class for all job providers.

#### Classes

##### `JobProvider`

Abstract base class defining the interface for job providers.

**Abstract Methods:**

###### `fetch_jobs() -> List[Dict[str, Any]]`
Must fetch jobs from the provider's API and return raw job data.

###### `get_required_columns() -> List[str]`
Must return list of required column names for this provider.

###### `create_job_link(job_data: Dict[str, Any]) -> str`
Must generate a direct link to the job listing.

**Example Implementation:**
```python
from src.pyjobber.providers.base import JobProvider

class MyProvider(JobProvider):
    def fetch_jobs(self):
        # Implement API fetching
        return [{'id': 1, 'title': 'Developer'}]
    
    def get_required_columns(self):
        return ['id', 'title']
    
    def create_job_link(self, job_data):
        return f"https://example.com/job/{job_data['id']}"
```

### `pyjobber.providers.bestjobs`

BestJobs.eu API integration.

#### Classes

##### `BestJobsProvider(JobProvider)`

Provider for BestJobs.eu job listings.

**Constructor:**
```python
BestJobsProvider(remote: bool = False)
```

**Parameters:**
- `remote` (bool): Whether to fetch only remote jobs

**Methods:**

###### `fetch_jobs() -> List[Dict[str, Any]]`
Fetches jobs from BestJobs.eu API with automatic pagination.

**Returns:**
- `List[Dict]`: Raw job data from API

**Data Structure:**
```python
{
    'id': int,
    'slug': str,
    'title': str,
    'companyName': str,
    'active': bool,
    'ownApplyUrl': str
}
```

###### `get_required_columns() -> List[str]`
Returns `['id', 'slug', 'title', 'companyName', 'active', 'ownApplyUrl']`

###### `create_job_link(job_data: Dict[str, Any]) -> str`
Generates BestJobs listing URL: `https://www.bestjobs.eu/loc-de-munca/{slug}`

**Example:**
```python
from src.pyjobber.providers.bestjobs import BestJobsProvider

provider = BestJobsProvider(remote=True)
jobs = provider.fetch_jobs()
link = provider.create_job_link(jobs[0])
```

### `pyjobber.providers.ejobs`

eJobs.ro API integration.

#### Classes

##### `EJobsProvider(JobProvider)`

Provider for eJobs.ro job listings.

**Methods:**

###### `fetch_jobs() -> List[Dict[str, Any]]`
Fetches jobs from eJobs.ro API with automatic pagination.

**Returns:**
- `List[Dict]`: Raw job data from API

**Data Structure:**
```python
{
    'id': int,
    'title': str,
    'slug': str,
    'creationDate': str,
    'expirationDate': str,
    'externalUrl': str
}
```

###### `create_job_link(job_data: Dict[str, Any]) -> str`
Generates eJobs listing URL: `https://www.ejobs.ro/user/locuri-de-munca/{slug}/{id}`

**Example:**
```python
from src.pyjobber.providers.ejobs import EJobsProvider

provider = EJobsProvider()
jobs = provider.fetch_jobs()
```

## Storage Module

### `pyjobber.storage.csv_handler`

CSV file operations and caching utilities.

#### Functions

##### `save_jobs_to_csv(df_bjobs: pd.DataFrame, df_ejobs: pd.DataFrame, external_jobs: Optional[pd.DataFrame] = None, cache_dir: str = "data/cache")`

Saves job DataFrames to CSV files.

**Parameters:**
- `df_bjobs`: BestJobs DataFrame
- `df_ejobs`: eJobs DataFrame  
- `external_jobs`: External jobs DataFrame (optional)
- `cache_dir`: Cache directory path

**Files Created:**
- `{cache_dir}/bjobs.csv`
- `{cache_dir}/ejobs.csv`
- `{cache_dir}/externalJobs.csv` (if external_jobs provided)

##### `load_jobs_from_csv(cache_dir: str = "data/cache") -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]`

Loads job DataFrames from CSV files.

**Parameters:**
- `cache_dir`: Cache directory path

**Returns:**
- `Tuple`: (bjobs_df, ejobs_df, external_jobs_df) or (None, None, None) if files missing

##### `csv_files_exist(cache_dir: str = "data/cache") -> bool`

Checks if required CSV files exist.

**Parameters:**
- `cache_dir`: Cache directory path

**Returns:**
- `bool`: True if bjobs.csv and ejobs.csv exist

**Example:**
```python
from src.pyjobber.storage.csv_handler import save_jobs_to_csv, load_jobs_from_csv, csv_files_exist

# Save data
save_jobs_to_csv(bjobs_df, ejobs_df, external_df)

# Check and load
if csv_files_exist():
    bjobs, ejobs, external = load_jobs_from_csv()
```

## Utils Module

### `pyjobber.utils.rate_limiter`

Rate limiting utilities for API management.

#### Functions

##### `check_last_run(timestamp_file: str = "last_run.txt") -> bool`

Checks if 24+ hours have passed since last successful run.

**Parameters:**
- `timestamp_file`: Path to timestamp file

**Returns:**
- `bool`: True if 24+ hours passed or first run, False otherwise

**Behavior:**
- Returns True on first run (no timestamp file)
- Calculates time difference from stored timestamp
- Prints remaining wait time if < 24 hours

##### `update_timestamp(timestamp_file: str = "last_run.txt")`

Updates timestamp file with current time.

**Parameters:**
- `timestamp_file`: Path to timestamp file

**Usage Pattern:**
```python
from src.pyjobber.utils.rate_limiter import check_last_run, update_timestamp

if check_last_run():
    try:
        # Perform API operations
        result = fetch_data()
        update_timestamp()  # Only on success
    except Exception:
        # Don't update timestamp on failure
        pass
```

## UI Module

### `pyjobber.ui.streamlit_app`

Streamlit web dashboard for viewing job data.

#### Functions

##### `run_streamlit_dashboard()`

Launches the Streamlit web interface for job data visualization.

**Features:**
- Checks for cached CSV files
- Displays jobs in organized tabs
- Shows job counts and summaries
- Handles missing data gracefully

**Usage:**
```python
# Called automatically when using streamlit
# uv run streamlit main.py --streamlit
```

**Dashboard Tabs:**
1. **BestJobs**: Displays BestJobs listings with company info
2. **eJobs**: Shows eJobs with creation/expiration dates  
3. **External Jobs**: Lists jobs with external application URLs

## Error Handling

All modules implement comprehensive error handling:

### Common Exceptions

- `requests.exceptions.RequestException`: Network/API errors
- `KeyError`: Missing required data fields
- `FileNotFoundError`: Missing configuration files
- `ValueError`: Invalid data formats
- `IOError`: File system errors

### Error Logging

All modules use print-based logging with prefixes:
- `[INFO]`: Informational messages
- `[WARNING]`: Non-fatal issues
- `[ERROR]`: Error conditions
- `[SUCCESS]`: Successful operations
- `[DEBUG]`: Debug information

### Best Practices

1. **Always handle exceptions** in provider implementations
2. **Log meaningful error messages** with context
3. **Don't update timestamps** on failures (rate limiting)
4. **Gracefully handle missing data** in UI components
5. **Validate data structures** before processing