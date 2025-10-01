import os
import pandas as pd


def save_jobs_to_csv(df_bjobs, df_ejobs, external_jobs=None, cache_dir="data/cache"):
    """Save job DataFrames to CSV files."""
    os.makedirs(cache_dir, exist_ok=True)
    
    df_bjobs.to_csv(os.path.join(cache_dir, 'bjobs.csv'), index=False)
    df_ejobs.to_csv(os.path.join(cache_dir, 'ejobs.csv'), index=False)
    
    if external_jobs is not None:
        external_jobs.to_csv(os.path.join(cache_dir, 'externalJobs.csv'), index=False)

    

def load_jobs_from_csv(cache_dir="data/cache"):
    """Load job DataFrames from CSV files."""
    bjobs_path = os.path.join(cache_dir, 'bjobs.csv')
    ejobs_path = os.path.join(cache_dir, 'ejobs.csv')
    external_path = os.path.join(cache_dir, 'externalJobs.csv')
    
    if not (os.path.exists(bjobs_path) and os.path.exists(ejobs_path)):
        return None, None, None
    
    df_bjobs = pd.read_csv(bjobs_path)
    df_ejobs = pd.read_csv(ejobs_path)
    external_jobs = pd.read_csv(external_path) if os.path.exists(external_path) else None
    
    return df_bjobs, df_ejobs, external_jobs


def csv_files_exist(cache_dir="data/cache"):
    """Check if the required CSV files exist."""
    bjobs_path = os.path.join(cache_dir, 'bjobs.csv')
    ejobs_path = os.path.join(cache_dir, 'ejobs.csv')
    return os.path.exists(bjobs_path) and os.path.exists(ejobs_path)