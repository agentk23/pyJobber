# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyJobber is a job scraping and filtering application that fetches job listings from Romanian job sites (bestjobs.eu and ejobs.ro), applies word-based filtering, and optionally displays results through Streamlit.

## Architecture

- **Main entry point**: `main.py` - command-line interface with scraping and Streamlit options
- **Core functionality**: `lib/linkProvider/linkProvider.py` - orchestrates the job fetching workflow with rate limiting (24-hour intervals)
- **API integration**: `lib/linkProvider/jobs.py` - handles API calls to job sites and data processing
- **Filtering**: `lib/linkProvider/bannedWords.txt` - contains words to filter out from job titles

## Key Components

### Rate Limiting System
The application uses timestamp-based rate limiting via `check_last_run()` in `linkProvider.py`, preventing API calls more than once per 24 hours. Results are cached as CSV files (`bjobs.csv`, `ejobs.csv`, `externalJobs.csv`). Timestamp is only updated on successful completion to allow retries on failures.

### Job Processing Pipeline
1. Fetch jobs from bestjobs.eu and ejobs.ro APIs with comprehensive error handling and logging
2. Filter job titles against banned words list (`bannedWords.txt`)
3. Extract relevant columns and generate direct job links
4. Save filtered results to CSV files
5. Optional Streamlit dashboard for data visualization

### Streamlit Dashboard
The application includes a web-based dashboard accessible via `streamlit run main.py --streamlit` that displays:
- BestJobs listings in organized tabs
- eJobs listings with creation dates
- External job URLs in a separate view
- Job counts and data summaries

## Development Commands

```bash
# Install dependencies
uv sync

# Run the job scraper (default behavior)
python main.py

# Explicitly run the job scraper
python main.py --scrape

# Run with Streamlit dashboard to view data
streamlit run main.py --streamlit

# Legacy method (still works)
python lib/linkProvider/linkProvider.py
```

## Data Flow

- APIs return different structures: bestjobs (id, slug, title, companyName, active, ownApplyUrl) vs ejobs (id, title, slug, creationDate, expirationDate, externalUrl)
- Both are normalized and filtered through the banned words system
- External application URLs are consolidated into `externalJobs.csv`
- Job site links are generated using site-specific URL patterns