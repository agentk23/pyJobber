# Multi-Threading Implementation in PyJobber

## Overview

PyJobber now supports multi-threaded operation, allowing the scraper to run in the background while the Streamlit UI remains responsive and displays job data in real-time.

## Architecture

### Components

1. **Background Scraper Service** (`src/pyjobber/core/background_scraper.py`)
   - Manages scraping in a separate thread
   - Thread-safe status tracking
   - Automatic rate limiting (24-hour interval)

2. **Enhanced Streamlit UI** (`src/pyjobber/ui/streamlit_app.py`)
   - Real-time scraper status display
   - Auto-refresh capability
   - Job selection and export features
   - Search and filter functionality

3. **Main Entry Point** (`main.py`)
   - Coordinates background scraper and UI
   - Multiple operation modes

## How It Works

### Application Flow

```
┌─────────────────┐
│  User starts    │
│  application    │
└────────┬────────┘
         │
         v
┌────────────────────────────┐
│  Check 24-hour rate limit  │
└────────┬───────────────────┘
         │
         ├─── YES (>24 hours) ───> Start background scraper thread
         │                          │
         └─── NO  (<24 hours) ───> Skip scraping
                                    │
         ┌──────────────────────────┘
         │
         v
┌────────────────────────┐
│  Start Streamlit UI    │  ◄─── Runs immediately,
│  (main thread)         │       doesn't wait for scraper
└────────┬───────────────┘
         │
         v
┌─────────────────────────────────┐
│  UI displays cached data         │
│  Shows scraper status            │
│  User can select jobs            │
│  User can export selections      │
└─────────────────────────────────┘
         │
         v
┌─────────────────────────────────┐
│  When scraping completes:        │
│  - New data saved to CSV         │
│  - UI can refresh to show new    │
│  - Timestamp updated             │
└─────────────────────────────────┘
```

### Thread Safety

The `ScraperStatus` class uses a threading lock to ensure thread-safe status updates:

```python
class ScraperStatus:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = "idle"
        # ...

    def set_status(self, status: str, progress: str = ""):
        with self._lock:
            self._status = status
            self._progress = progress
```

### Background Scraper States

1. **idle** - No scraping needed (rate limit not reached)
2. **running** - Actively scraping APIs
3. **completed** - Scraping finished successfully
4. **failed** - Scraping encountered an error

## Usage

### Basic Usage (Recommended)

Start with multi-threading enabled:

```bash
streamlit run main.py
```

This will:
- Check if 24 hours have passed since last scrape
- Start background scraping if needed
- Launch Streamlit UI immediately
- Display cached data while scraping
- Update when new data is available

### Alternative Modes

#### 1. Explicit Multi-threaded Mode

```bash
python main.py --streamlit
```

Same as above, but using the `--streamlit` flag.

#### 2. Disable Background Scraping

```bash
python main.py --streamlit --no-background
```

Launches UI without starting background scraper.

#### 3. Foreground Scraping Only

```bash
python main.py --scrape
```

Runs scraper in foreground (blocks until complete), no UI.

#### 4. Force Re-scrape

```bash
# Remove rate limit timestamp
python main.py --force

# Then run normally
streamlit run main.py
```

### UI Features

#### 1. Scraper Status Display

The UI shows real-time scraper status:
- 🔄 **Running** - Scraping in progress with elapsed time
- ✅ **Completed** - Scraping finished with duration
- ❌ **Failed** - Error message displayed
- 💤 **Idle** - Using cached data

#### 2. Auto-Refresh

Enable auto-refresh to automatically update the UI every 5 seconds:

```
☑️ Auto-refresh (5s)
```

Useful when scraping is in progress to see when new data arrives.

#### 3. Manual Refresh

Click the "🔄 Refresh Now" button to reload data from CSV files.

#### 4. Job Selection & Export

**In the "External Jobs" tab:**

1. Browse jobs with external application URLs
2. Use search to filter by title
3. Check the "✅ Select" column for jobs you want
4. Preview selected jobs in the expander
5. Click "📥 Export Selected" to save to CSV

**Export location:**
```
data/selected/selected_jobs_export.csv
```

#### 5. Search & Filter

Each tab has a search box to filter jobs:
- **BestJobs**: Search by title or company name
- **eJobs**: Search by title
- **External Jobs**: Search by title

## Code Examples

### Starting Background Scraper Programmatically

```python
from pyjobber.core.background_scraper import start_background_scraper

# Start the scraper
scraper = start_background_scraper()

# Check if it's running
if scraper.status.is_running():
    print("Scraping in progress...")

# Get status information
status_info = scraper.get_status_info()
print(f"Status: {status_info['status']}")
print(f"Progress: {status_info['progress']}")

# Wait for completion (optional)
scraper.wait_for_completion(timeout=300)  # 5 minutes
```

### Accessing Global Scraper Instance

```python
from pyjobber.core.background_scraper import get_background_scraper

# Get the global scraper instance
scraper = get_background_scraper()

# Check status
if scraper.status.is_completed():
    print("Scraping completed!")
elif scraper.status.is_running():
    print("Still scraping...")
```

## Technical Details

### Threading Model

- **Main Thread**: Runs Streamlit UI (must be main thread for Streamlit)
- **Background Thread**: Runs scraper (daemon thread)
- **Global State**: Single `BackgroundScraper` instance shared across app

### Rate Limiting

Rate limiting is preserved in multi-threaded mode:
- Checks `last_run.txt` before starting scraper
- Only scrapes if 24+ hours have passed
- Updates timestamp on successful completion
- Does not update timestamp on failure

### Error Handling

```python
try:
    df_bjobs, df_ejobs, external_jobs = scrape_jobs()
    save_jobs_to_csv(df_bjobs, df_ejobs, external_jobs)
    update_timestamp()
    status.set_status("completed", "Success message")
except Exception as e:
    status.set_error(e)
    # Timestamp NOT updated on failure
```

### CSV File Structure

**Cached data:** `data/cache/`
- `bjobs.csv` - BestJobs listings
- `ejobs.csv` - eJobs listings
- `externalJobs.csv` - Jobs with external URLs

**Selected exports:** `data/selected/`
- `selected_jobs_export.csv` - User-selected jobs for export

## Performance Considerations

### Memory Usage

- Background thread shares memory with main process
- DataFrames are loaded in main thread (not duplicated)
- Minimal overhead from status tracking

### Startup Time

**Without multi-threading:**
```
Wait for scraping (60-120s) → Launch UI → Display data
```

**With multi-threading:**
```
Launch UI immediately (<1s) → Display cached data → Update when scraping completes
```

**Improvement:** User sees UI immediately instead of waiting 1-2 minutes.

### CPU Usage

- Scraping thread uses CPU for HTTP requests and data processing
- UI thread uses CPU for rendering
- Both threads can run concurrently on multi-core systems

## Troubleshooting

### Issue: UI doesn't show scraper status

**Solution:** Ensure you're using the default or `--streamlit` mode. Background scraper only starts in these modes.

### Issue: Scraper keeps saying "idle"

**Cause:** 24 hours haven't passed since last scrape.

**Solution:**
```bash
python main.py --force
streamlit run main.py
```

### Issue: UI shows old data after scraping completes

**Solution:** Click "🔄 Refresh Now" or enable auto-refresh.

### Issue: Export fails with "directory not found"

**Cause:** The `data/selected/` directory doesn't exist.

**Solution:** It's created automatically, but you can create manually:
```bash
mkdir -p data/selected
```

### Issue: Background thread hangs

**Cause:** API timeout or network issue.

**Solution:** The thread is marked as daemon and will terminate when the main program exits. Restart the application.

## Best Practices

1. **Use auto-refresh during scraping** - Enable auto-refresh to see when new data arrives
2. **Check scraper status** - Look at the status banner before expecting fresh data
3. **Wait for completion** - If you need fresh data, wait for "✅ Completed" status
4. **Export regularly** - Export selected jobs before refreshing to avoid losing selections
5. **Monitor console output** - Watch the terminal for detailed scraping progress

## Future Enhancements

Potential improvements to the multi-threading implementation:

- [ ] Progress bar showing scraping percentage
- [ ] Real-time job count updates during scraping
- [ ] WebSocket-based live updates (instead of polling/refresh)
- [ ] Parallel scraping of multiple providers
- [ ] Background job for periodic auto-scraping
- [ ] Notification when scraping completes
- [ ] Retry mechanism for failed scrapes

## See Also

- [README.md](../README.md) - Main documentation
- [CHANGES.md](../CHANGES.md) - Version history
- [tests/README.md](../tests/README.md) - Testing documentation
