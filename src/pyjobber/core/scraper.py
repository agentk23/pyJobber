import pandas as pd
from typing import Tuple, Optional

from ..providers.bestjobs import BestJobsProvider
from ..providers.ejobs import EJobsProvider
from ..storage.csv_handler import save_jobs_to_csv, load_jobs_from_csv, csv_files_exist
from ..utils.rate_limiter import check_last_run, update_timestamp
from .filters import filter_jobs_by_banned_words


def scrape_jobs() -> Tuple:
    """Main job scraping function."""
    print("[INFO] Starting job scraping process...")
    
    try:
        # Initialize providers
        bestjobs_provider = BestJobsProvider()
        ejobs_provider = EJobsProvider()
        
        # Fetch BestJobs data
        print("\n=== FETCHING BESTJOBS DATA ===")
        bestjobs_data = bestjobs_provider.fetch_jobs()
        df_bjobs = pd.DataFrame(bestjobs_data)
        
        required_bjobs_cols = bestjobs_provider.get_required_columns()
        missing_cols = [col for col in required_bjobs_cols if col not in df_bjobs.columns]
        if missing_cols:
            print(f"[WARNING] Missing columns in BestJobs data: {missing_cols}")
            print(f"[INFO] Available columns: {list(df_bjobs.columns)}")
        
        df_bjobs = df_bjobs[required_bjobs_cols]
        print(f"[INFO] Processed {len(df_bjobs)} BestJobs entries")

        # Fetch eJobs data
        print("\n=== FETCHING EJOBS DATA ===")
        ejobs_data = ejobs_provider.fetch_jobs()
        df_ejobs = pd.DataFrame(ejobs_data)
        
        if len(df_ejobs) == 0:
            print("[WARNING] No eJobs data retrieved, creating empty DataFrame")
            df_ejobs = pd.DataFrame(columns=ejobs_provider.get_required_columns())
        else:
            required_ejobs_cols = ejobs_provider.get_required_columns()
            missing_cols = [col for col in required_ejobs_cols if col not in df_ejobs.columns]
            if missing_cols:
                print(f"[WARNING] Missing columns in eJobs data: {missing_cols}")
                print(f"[INFO] Available columns: {list(df_ejobs.columns)}")
            
            df_ejobs = df_ejobs[required_ejobs_cols]
            df_ejobs = df_ejobs.sort_values(by='creationDate')
            print(f"[INFO] Processed {len(df_ejobs)} eJobs entries")

        # Apply word filtering
        print("\n=== APPLYING WORD FILTERS ===")
        initial_bjobs_count = len(df_bjobs)
        initial_ejobs_count = len(df_ejobs)
        
        df_bjobs = filter_jobs_by_banned_words(df_bjobs)
        df_ejobs = filter_jobs_by_banned_words(df_ejobs)
        
        print(f"[INFO] BestJobs: {initial_bjobs_count} -> {len(df_bjobs)} jobs (filtered {initial_bjobs_count - len(df_bjobs)})")
        print(f"[INFO] eJobs: {initial_ejobs_count} -> {len(df_ejobs)} jobs (filtered {initial_ejobs_count - len(df_ejobs)})")

        # Generate job links
        print("\n=== GENERATING LINKS ===")
        bjobs_links = df_bjobs.apply(lambda x: bestjobs_provider.create_job_link(x), axis=1)
        ejobs_links = df_ejobs.apply(lambda x: ejobs_provider.create_job_link(x), axis=1)

        # Prepare final DataFrames
        print("\n=== PREPARING FINAL DATA ===")
        df_bjobs = df_bjobs[['title', 'companyName', 'ownApplyUrl']].copy()
        df_ejobs = df_ejobs[['title', 'creationDate', 'expirationDate', 'externalUrl']].copy()
        df_ejobs = df_ejobs.rename(columns={"externalUrl": "ownApplyUrl"})
        
        # Create external jobs DataFrame
        df_external_ejobs = df_ejobs[df_ejobs['ownApplyUrl'].notna() & (df_ejobs['ownApplyUrl'] != '')]
        df_external_bjobs = df_bjobs[df_bjobs['ownApplyUrl'].notna() & (df_bjobs['ownApplyUrl'] != '')]
        
        if len(df_external_ejobs) > 0 or len(df_external_bjobs) > 0:
            external_jobs = pd.concat([df_external_ejobs, df_external_bjobs], ignore_index=True)
            print(f"[INFO] Created external jobs DataFrame with {len(external_jobs)} entries")
        else:
            external_jobs = None
            print("[INFO] No external job URLs found")

        # Add generated links to DataFrames
        df_bjobs['link'] = bjobs_links
        df_ejobs['link'] = ejobs_links
        
        print("\n[SUCCESS] Job scraping completed successfully!")
        print(f"[SUMMARY] Final counts - BestJobs: {len(df_bjobs)}, eJobs: {len(df_ejobs)}")
        
        return df_bjobs, df_ejobs, external_jobs
        
    except Exception as e:
        print(f"[ERROR] Fatal error in scrape_jobs: {e}")
        raise


def run_scraper_or_load_cache():
    """Main orchestration function that handles rate limiting and caching."""
    if check_last_run():
        print("24+ hours have passed. Running scraper...")
        try:
            df_bjobs, df_ejobs, external_jobs = scrape_jobs()
            save_jobs_to_csv(df_bjobs, df_ejobs, external_jobs)
            update_timestamp()
            print("Scraping completed successfully.")
            return df_bjobs, df_ejobs, external_jobs
        except Exception as e:
            print(f"Scraping failed with error: {e}")
            print("Timestamp not updated due to failure.")
            return None, None, None
    else:
        if csv_files_exist():
            df_bjobs, df_ejobs, external_jobs = load_jobs_from_csv()
            print("CSV files found. Loading cached data.")
            return df_bjobs, df_ejobs, external_jobs
        else:
            print("No CSV files found. Please run the scraper after 24 hours or manually.")
            return None, None, None