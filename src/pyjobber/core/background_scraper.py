"""Background scraper service with threading support."""
import threading
import time
from typing import Optional, Tuple
import pandas as pd
from datetime import datetime

from ..utils.rate_limiter import check_last_run, update_timestamp
from ..storage.csv_handler import save_jobs_to_csv
from .scraper import scrape_jobs


class ScraperStatus:
    """Thread-safe scraper status tracking."""

    def __init__(self):
        self._lock = threading.Lock()
        self._status = "idle"  # idle, running, completed, failed
        self._progress = ""
        self._error = None
        self._start_time = None
        self._end_time = None

    def set_status(self, status: str, progress: str = ""):
        """Set scraper status and progress message."""
        with self._lock:
            self._status = status
            self._progress = progress
            if status == "running" and self._start_time is None:
                self._start_time = datetime.now()
            elif status in ["completed", "failed"]:
                self._end_time = datetime.now()

    def set_error(self, error: Exception):
        """Set error information."""
        with self._lock:
            self._error = error
            self._status = "failed"

    def get_status(self) -> dict:
        """Get current status information."""
        with self._lock:
            return {
                "status": self._status,
                "progress": self._progress,
                "error": str(self._error) if self._error else None,
                "start_time": self._start_time,
                "end_time": self._end_time,
                "duration": (self._end_time - self._start_time).total_seconds()
                           if self._start_time and self._end_time else None
            }

    def is_running(self) -> bool:
        """Check if scraper is currently running."""
        with self._lock:
            return self._status == "running"

    def is_completed(self) -> bool:
        """Check if scraper completed successfully."""
        with self._lock:
            return self._status == "completed"


class BackgroundScraper:
    """Manages background scraping in a separate thread."""

    def __init__(self):
        self.status = ScraperStatus()
        self.thread: Optional[threading.Thread] = None

    def should_run_scraper(self) -> bool:
        """Check if scraper should run based on rate limit."""
        return check_last_run()

    def _scrape_worker(self):
        """Worker function that runs in background thread."""
        try:
            self.status.set_status("running", "Starting job scraping...")

            # Run the scraper
            self.status.set_status("running", "Fetching jobs from providers...")
            df_bjobs, df_ejobs, external_jobs = scrape_jobs()

            # Save to CSV
            self.status.set_status("running", "Saving jobs to CSV...")
            save_jobs_to_csv(df_bjobs, df_ejobs, external_jobs)

            # Update timestamp
            self.status.set_status("running", "Updating timestamp...")
            update_timestamp()

            self.status.set_status("completed", f"Successfully scraped {len(df_bjobs)} BestJobs and {len(df_ejobs)} eJobs")
            print(f"[Background Scraper] Completed successfully at {datetime.now()}")

        except Exception as e:
            self.status.set_error(e)
            print(f"[Background Scraper] Failed with error: {e}")

    def start(self):
        """Start the background scraper if needed."""
        if not self.should_run_scraper():
            self.status.set_status("idle", "Rate limit not reached - using cached data")
            print("[Background Scraper] Skipping scrape - 24 hours not elapsed")
            return False

        if self.thread and self.thread.is_alive():
            print("[Background Scraper] Already running")
            return False

        print("[Background Scraper] Starting background scraping thread...")
        self.status.set_status("running", "Initializing scraper...")
        self.thread = threading.Thread(target=self._scrape_worker, daemon=True)
        self.thread.start()
        return True

    def wait_for_completion(self, timeout: Optional[float] = None):
        """Wait for scraper thread to complete."""
        if self.thread:
            self.thread.join(timeout=timeout)

    def get_status_info(self) -> dict:
        """Get current scraper status information."""
        return self.status.get_status()


# Global scraper instance for sharing across application
_background_scraper: Optional[BackgroundScraper] = None


def get_background_scraper() -> BackgroundScraper:
    """Get or create the global background scraper instance."""
    global _background_scraper
    if _background_scraper is None:
        _background_scraper = BackgroundScraper()
    return _background_scraper


def start_background_scraper() -> BackgroundScraper:
    """Start the background scraper and return the instance."""
    scraper = get_background_scraper()
    scraper.start()
    return scraper
