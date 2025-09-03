import time
import requests
from typing import List, Dict, Any
from .base import JobProvider


class EJobsProvider(JobProvider):
    """Provider for eJobs.ro API."""
    
    def __init__(self):
        self.base_url = "https://api.ejobs.ro/jobs"
    
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """Fetch jobs from eJobs API."""
        print("[INFO] Starting eJobs API request...")
        page = 1
        results = []
        
        try:
            while True:
                url = f"{self.base_url}?page={page}&pageSize=100&filters.cities=381&filters.cities=1&filters.careerLevels=10&filters.careerLevels=3&filters.careerLevels=4&sort=suitability"
                print(f"[INFO] Fetching eJobs page {page}...")
                
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                response_data = response.json()
                
                if 'jobs' not in response_data:
                    print(f"[WARNING] 'jobs' key missing on page {page}, stopping pagination")
                    break
                
                current_jobs = response_data['jobs']
                results.extend(current_jobs)
                print(f"[INFO] Added {len(current_jobs)} jobs from page {page}, total so far: {len(results)}")
                
                # Check if more pages exist
                if not response_data.get('morePagesFollow', False):
                    break
                
                page += 1
                time.sleep(5)
            
            print(f"[SUCCESS] Retrieved {len(results)} total jobs from eJobs")
            return results
            
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Network error while fetching eJobs: {e}")
            raise
        except KeyError as e:
            print(f"[ERROR] Missing key in eJobs API response: {e}")
            raise
        except Exception as e:
            print(f"[ERROR] Unexpected error in eJobs request: {e}")
            raise
    
    def get_required_columns(self) -> List[str]:
        """Get required columns for eJobs data."""
        return ['id', 'title', 'slug', 'creationDate', 'expirationDate', 'externalUrl']
    
    def create_job_link(self, job_data: Dict[str, Any]) -> str:
        """Create a direct link to the eJobs listing."""
        return f'https://www.ejobs.ro/user/locuri-de-munca/{job_data["slug"]}/{job_data["id"]}'