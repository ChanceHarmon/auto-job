from abc import ABC, abstractmethod

from auto_job.config import AppConfig
from auto_job.models import Job


class JobSource(ABC):
    """Base class for all job sources."""

    name: str

    def __init__(self, config: AppConfig):
        self.config = config

    @abstractmethod
    def fetch_jobs(self) -> list[Job]:
        """Fetch jobs from this source and return normalized Job objects."""
        pass