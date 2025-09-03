import argparse
import sys
import os

# Add src to Python path so we can import pyjobber
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from pyjobber.core.scraper import run_scraper_or_load_cache
from pyjobber.ui.streamlit_app import run_streamlit_dashboard


def main():
    parser = argparse.ArgumentParser(description="PyJobber - Job scraper and viewer")
    parser.add_argument('--scrape', action='store_true', help='Run the job scraper')
    parser.add_argument('--streamlit', action='store_true', help='Run in Streamlit mode (use: uv run streamlit run main.py --streamlit)')
    parser.add_argument('--force', action='store_true', help='Force re-scrape of jobs')
    args = parser.parse_args()
    
    if args.streamlit:
        run_streamlit_dashboard()
    elif args.scrape:
        result = run_scraper_or_load_cache()
        if result[0] is None:
            sys.exit(1)
    elif args.force:
        if os.path.exists('last_run.txt'):
            os.remove('last_run.txt')
    else:
        # Default behavior - just run scraper
        result = run_scraper_or_load_cache()
        if result[0] is None:
            sys.exit(1)


if __name__ == "__main__":
    main()