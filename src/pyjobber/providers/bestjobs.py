import time
import requests
from typing import List, Dict, Any
from .base import JobProvider


class BestJobsProvider(JobProvider):
    """Provider for BestJobs.eu API."""
    
    def __init__(self, remote=False):
        self.remote = remote
        self.base_url = "https://api.bestjobs.eu/v1/jobs"
    
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """Fetch jobs from BestJobs API."""
        print("[INFO] Starting BestJobs API request...")
        try:
            # Initial request to get total count
            url = f"{self.base_url}?offset=0&limit=24&remote={(1 if self.remote else 0)}"
            print(f"[INFO] Making initial request to: {url}")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'total' not in result:
                raise KeyError("'total' key not found in BestJobs API response")
            
            total_jobs = result['total']
            print(f"[INFO] Found {total_jobs} total jobs, fetching all...")
            
            # Fetch all jobs
            url = f"{self.base_url}?offset=0&limit={total_jobs}&remote=1"
            print(f"[INFO] Making full request to: {url}")
            time.sleep(5)
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'items' not in result:
                raise KeyError("'items' key not found in BestJobs API response")
            
            jobs = result['items']
            print(f"[SUCCESS] Retrieved {len(jobs)} jobs from BestJobs")
            return jobs
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network error while fetching BestJobs: {e}")
            raise
        except KeyError as e:
            print(f"[ERROR] Missing key in BestJobs API response: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Unexpected error in BestJobs request: {e}")
            raise
    
    def get_required_columns(self) -> List[str]:
        """Get required columns for BestJobs data."""
        return ['id', 'slug', 'title', 'companyName', 'active', 'ownApplyUrl']
    
    def create_job_link(self, job_data: Dict[str, Any]) -> str:
        """Create a direct link to the BestJobs listing."""
        return f'https://www.bestjobs.eu/loc-de-munca/{job_data["slug"]}'