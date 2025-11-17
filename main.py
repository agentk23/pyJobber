import argparse
import sys
import os

# Add src to Python path so we can import pyjobber
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyjobber.core.scraper import run_scraper_or_load_cache
from pyjobber.ui.streamlit_app import run_streamlit_dashboard
from pyjobber.core.background_scraper import start_background_scraper


def main():
    parser = argparse.ArgumentParser(
        description="PyJobber - Job scraper and viewer with multi-threading support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with automatic background scraping and UI
  streamlit run main.py

  # Run only the scraper
  python main.py --scrape

  # Force re-scrape (removes rate limit)
  python main.py --force

  # Run in Streamlit mode (with background scraping)
  python main.py --streamlit
        """
    )
    parser.add_argument('--scrape', action='store_true',
                       help='Run the job scraper only (no UI)')
    parser.add_argument('--streamlit', action='store_true',
                       help='Run in Streamlit mode with background scraping')
    parser.add_argument('--force', action='store_true',
                       help='Force re-scrape by removing rate limit timestamp')
    parser.add_argument('--no-background', action='store_true',
                       help='Disable background scraping when running Streamlit')
    args = parser.parse_args()

    if args.force:
        # Force re-scrape by removing timestamp
        if os.path.exists('last_run.txt'):
            os.remove('last_run.txt')
            print("[INFO] Rate limit timestamp removed. Next run will scrape.")
        else:
            print("[INFO] No timestamp file found.")
        return

    if args.streamlit:
        # Multi-threaded mode: Start background scraper + Streamlit UI
        print("[INFO] Starting PyJobber in multi-threaded mode...")

        if not args.no_background:
            print("[INFO] Initializing background scraper...")
            scraper = start_background_scraper()

            if scraper.status.is_running():
                print("[INFO] Background scraping started")
            else:
                status_info = scraper.get_status_info()
                print(f"[INFO] Scraper status: {status_info['status']} - {status_info['progress']}")
        else:
            print("[INFO] Background scraping disabled")

        print("[INFO] Starting Streamlit UI...")
        run_streamlit_dashboard()

    elif args.scrape:
        # Legacy mode: Run scraper only
        print("[INFO] Running scraper in foreground mode...")
        result = run_scraper_or_load_cache()
        if result[0] is None:
            print("[ERROR] Scraping failed")
            sys.exit(1)
        print("[SUCCESS] Scraping completed")

    else:
        # Default behavior when run with streamlit command
        # This is triggered when using: streamlit run main.py
        print("[INFO] Starting PyJobber in default mode...")
        print("[INFO] Initializing background scraper...")

        scraper = start_background_scraper()

        if scraper.status.is_running():
            print("[INFO] Background scraping started - UI will load immediately")
        else:
            status_info = scraper.get_status_info()
            print(f"[INFO] Scraper status: {status_info['status']}")
            print(f"[INFO] {status_info['progress']}")

        run_streamlit_dashboard()


if __name__ == "__main__":
    main()