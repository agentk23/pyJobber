from abc import ABC, abstractmethod
from typing import List, Dict, Any


class JobProvider(ABC):
    """Base class for job providers."""
    
    @abstractmethod
    def fetch_jobs(self) -> List[Dict[str, Any]]:
        """Fetch jobs from the provider."""
        pass
    
    @abstractmethod
    def get_required_columns(self) -> List[str]:
        """Get the required columns for this provider."""
        pass
    
    @abstractmethod
    def create_job_link(self, job_data: Dict[str, Any]) -> str:
        """Create a direct link to the job."""
        pass