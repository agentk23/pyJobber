# Configuration Guide

This document covers all configuration options and data formats used in PyJobber.

## Table of Contents

- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Data Formats](#data-formats)
- [Cache Management](#cache-management)
- [Customization Options](#customization-options)

## Configuration Files

### Banned Words Configuration

**File:** `data/banned_words.txt`

This file contains words and phrases that will filter out jobs from results. Each line represents a separate filter term.

**Format:**
```text
sales
marketing
manager
consultant
senior consultant
team lead
```

**Rules:**
- One word/phrase per line
- Case-insensitive matching
- Partial matches (e.g., "sales" matches "Senior Sales Executive")
- Empty lines and whitespace are ignored
- No special characters or regex needed

**Example Configuration:**
```text
# Sales and marketing roles
sales
marketing
commercial
business development

# Management positions
manager
director
executive
team lead
supervisor

# Consulting roles
consultant
advisory
consulting

# Industries to avoid
insurance
pharmaceutical
real estate
banking

# Job types to avoid
internship
volunteer
part-time
contract
freelance
```

**Best Practices:**
- Use specific terms to avoid over-filtering
- Test filter effectiveness by checking job counts before/after
- Keep a backup of working configurations
- Review and update filters periodically

### Rate Limiting Configuration

**File:** `last_run.txt` (auto-generated)

Contains ISO format timestamp of last successful scraping run.

**Format:**
```text
2024-01-15T14:30:45.123456
```

**Manual Override:**
To force a new scrape (for testing), delete this file or modify the timestamp:
```bash
# Delete to force fresh scrape
rm last_run.txt

# Or set to old timestamp
echo "2024-01-01T00:00:00.000000" > last_run.txt
```

## Environment Variables

### Optional Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `PYJOBBER_CACHE_DIR` | Cache directory path | `data/cache` | `/var/cache/pyjobber` |
| `PYJOBBER_BANNED_WORDS_FILE` | Banned words file path | `data/banned_words.txt` | `/etc/pyjobber/banned.txt` |
| `PYJOBBER_RATE_LIMIT_HOURS` | Rate limit interval | `24` | `12` |
| `PYJOBBER_LOG_LEVEL` | Logging verbosity | `INFO` | `DEBUG` |

### Usage Examples

**Production Deployment:**
```bash
export PYJOBBER_CACHE_DIR="/var/cache/pyjobber"
export PYJOBBER_BANNED_WORDS_FILE="/etc/pyjobber/banned_words.txt"
export PYJOBBER_RATE_LIMIT_HOURS="24"
```

**Development/Testing:**
```bash
export PYJOBBER_RATE_LIMIT_HOURS="0.1"  # 6 minutes
export PYJOBBER_LOG_LEVEL="DEBUG"
```

**Docker Environment:**
```dockerfile
ENV PYJOBBER_CACHE_DIR=/app/cache
ENV PYJOBBER_BANNED_WORDS_FILE=/app/config/banned_words.txt
```

## Data Formats

### Input Data Formats

#### BestJobs API Response
```json
{
  "total": 150,
  "items": [
    {
      "id": 12345,
      "slug": "software-engineer-python-bucharest",
      "title": "Software Engineer - Python",
      "companyName": "TechCorp SRL",
      "active": true,
      "ownApplyUrl": "https://techcorp.com/careers/apply/12345",
      "location": "Bucharest",
      "createdAt": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Required Fields:**
- `id` (int): Unique job identifier
- `slug` (str): URL-friendly job identifier
- `title` (str): Job title
- `companyName` (str): Company name
- `active` (bool): Job availability status
- `ownApplyUrl` (str): External application URL

#### eJobs API Response
```json
{
  "jobs": [
    {
      "id": 67890,
      "title": "Full Stack Developer",
      "slug": "full-stack-developer-react-node",
      "creationDate": "2024-01-15",
      "expirationDate": "2024-02-15",
      "externalUrl": "https://company.com/jobs/67890",
      "company": {
        "name": "Startup Inc"
      }
    }
  ],
  "morePagesFollow": true,
  "totalCount": 500
}
```

**Required Fields:**
- `id` (int): Unique job identifier
- `title` (str): Job title
- `slug` (str): URL-friendly identifier
- `creationDate` (str): Job posting date (YYYY-MM-DD)
- `expirationDate` (str): Job expiration date (YYYY-MM-DD)
- `externalUrl` (str): External application URL

### Output Data Formats

#### BestJobs CSV (`data/cache/bjobs.csv`)
```csv
title,companyName,ownApplyUrl,link
"Software Engineer - Python",TechCorp SRL,https://techcorp.com/careers/apply/12345,https://www.bestjobs.eu/loc-de-munca/software-engineer-python-bucharest
"Frontend Developer",WebAgency,https://webagency.ro/jobs/frontend,https://www.bestjobs.eu/loc-de-munca/frontend-developer-react-vue
```

**Columns:**
- `title`: Filtered job title
- `companyName`: Company name
- `ownApplyUrl`: External application URL (may be empty)
- `link`: Direct link to BestJobs listing

#### eJobs CSV (`data/cache/ejobs.csv`)
```csv
title,creationDate,expirationDate,ownApplyUrl,link
"Full Stack Developer","2024-01-15","2024-02-15",https://company.com/jobs/67890,https://www.ejobs.ro/user/locuri-de-munca/full-stack-developer-react-node/67890
"DevOps Engineer","2024-01-14","2024-02-14",,https://www.ejobs.ro/user/locuri-de-munca/devops-engineer-aws-kubernetes/67891
```

**Columns:**
- `title`: Filtered job title
- `creationDate`: Job posting date
- `expirationDate`: Job expiration date
- `ownApplyUrl`: External application URL (may be empty)
- `link`: Direct link to eJobs listing

#### External Jobs CSV (`data/cache/externalJobs.csv`)
```csv
title,creationDate,expirationDate,ownApplyUrl
"Full Stack Developer","2024-01-15","2024-02-15",https://company.com/jobs/67890
"Software Engineer - Python",,,https://techcorp.com/careers/apply/12345
```

**Purpose:** Consolidates all jobs that have external application URLs for easy access.

### Data Processing Pipeline

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Raw API       │    │    Validation    │    │   Column        │
│   Response      │───▶│   & Cleaning     │───▶│   Selection     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌───────▼─────────┐
│   CSV Export    │    │   Link           │    │   Banned Words  │
│   (Final)       │◀───│   Generation     │◀───│   Filtering     │
│                 │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

**Processing Steps:**
1. **API Fetch**: Raw JSON data from providers
2. **Validation**: Check required fields exist
3. **Column Selection**: Extract only needed columns
4. **Banned Words Filtering**: Remove unwanted jobs
5. **Link Generation**: Create direct job listing URLs
6. **CSV Export**: Save processed data to cache

## Cache Management

### Cache Structure
```
data/cache/
├── bjobs.csv           # BestJobs processed data
├── ejobs.csv           # eJobs processed data
└── externalJobs.csv    # Jobs with external URLs
```

### Cache Lifecycle

1. **Creation**: Generated after successful scraping
2. **Validation**: Checked for existence and readability
3. **Usage**: Loaded when rate limiting prevents fresh scraping
4. **Refresh**: Overwritten when new scraping occurs

### Cache Configuration

```python
# Default cache settings
CACHE_DIR = "data/cache"
CACHE_FILES = {
    'bestjobs': 'bjobs.csv',
    'ejobs': 'ejobs.csv', 
    'external': 'externalJobs.csv'
}

# Programmatic cache management
from src.pyjobber.storage.csv_handler import (
    save_jobs_to_csv, 
    load_jobs_from_csv,
    csv_files_exist
)

# Check cache status
if csv_files_exist():
    print("Cache available")
    bjobs, ejobs, external = load_jobs_from_csv()
else:
    print("Cache missing - fresh scraping required")
```

### Manual Cache Operations

```bash
# Check cache status
ls -la data/cache/

# View cache contents
head -5 data/cache/bjobs.csv
wc -l data/cache/*.csv

# Clear cache (force fresh scraping)
rm -rf data/cache/*.csv

# Backup cache
tar -czf cache-backup-$(date +%Y%m%d).tar.gz data/cache/
```

## Customization Options

### Custom Filter Functions

Create additional filtering logic:

```python
# src/pyjobber/core/custom_filters.py
import pandas as pd

def filter_by_salary(df: pd.DataFrame, min_salary: int = None) -> pd.DataFrame:
    """Filter jobs by minimum salary requirement."""
    if 'salary' not in df.columns:
        return df
    
    if min_salary:
        return df[df['salary'] >= min_salary]
    return df

def filter_by_experience(df: pd.DataFrame, max_experience: int = None) -> pd.DataFrame:
    """Filter jobs by maximum experience requirement."""
    if 'experience_years' not in df.columns:
        return df
        
    if max_experience:
        return df[df['experience_years'] <= max_experience]
    return df
```

### Custom Provider Implementation

Add support for new job sites:

```python
# src/pyjobber/providers/custom_site.py
from .base import JobProvider
import requests

class CustomSiteProvider(JobProvider):
    def __init__(self, api_endpoint: str, api_key: str = None):
        self.api_endpoint = api_endpoint
        self.api_key = api_key
    
    def fetch_jobs(self):
        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        response = requests.get(self.api_endpoint, headers=headers)
        return response.json()['data']
    
    def get_required_columns(self):
        return ['id', 'title', 'company', 'url']
    
    def create_job_link(self, job_data):
        return job_data['url']
```

### Configuration File Support

For complex configurations, create JSON config:

```json
// config/settings.json
{
  "scraping": {
    "rate_limit_hours": 24,
    "max_retries": 3,
    "timeout_seconds": 30
  },
  "filtering": {
    "banned_words_file": "data/banned_words.txt",
    "min_salary": 30000,
    "max_experience_years": 10,
    "allowed_locations": ["Bucharest", "Cluj", "Remote"]
  },
  "storage": {
    "cache_dir": "data/cache",
    "backup_enabled": true,
    "compression": "gzip"
  },
  "providers": {
    "bestjobs": {
      "enabled": true,
      "remote_only": false
    },
    "ejobs": {
      "enabled": true,
      "cities": ["Bucharest", "Cluj"]
    }
  }
}
```

```python
# Load configuration
import json

def load_config(config_file="config/settings.json"):
    with open(config_file, 'r') as f:
        return json.load(f)

config = load_config()
rate_limit = config['scraping']['rate_limit_hours']
```

### Environment-Specific Configurations

**Development:**
```bash
# .env.development
PYJOBBER_RATE_LIMIT_HOURS=0.1
PYJOBBER_LOG_LEVEL=DEBUG
PYJOBBER_CACHE_DIR=./dev-cache
```

**Production:**
```bash
# .env.production  
PYJOBBER_RATE_LIMIT_HOURS=24
PYJOBBER_LOG_LEVEL=INFO
PYJOBBER_CACHE_DIR=/var/cache/pyjobber
```

**Testing:**
```bash
# .env.test
PYJOBBER_RATE_LIMIT_HOURS=0
PYJOBBER_BANNED_WORDS_FILE=tests/fixtures/test_banned_words.txt
PYJOBBER_CACHE_DIR=./test-cache
```

This configuration guide provides complete control over PyJobber's behavior through various configuration mechanisms, from simple text files to complex JSON configurations and environment variables.