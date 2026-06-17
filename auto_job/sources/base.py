from abc import ABC, abstractmethod

from auto_job.config import AppConfig
from auto_job.models import Job


class JobSource(ABC):
    """Base contract every source adapter follows."""

    name: str

    def __init__(self, config: AppConfig):
        # Sources receive full app config so each adapter can read only the
        # provider-specific entries it needs.
        self.config = config

    @abstractmethod
    def fetch_jobs(self) -> list[Job]:
        """Fetch jobs from this source and return normalized Job objects."""
        pass
