from datetime import date

from pydantic import BaseModel, HttpUrl, Field


class Job(BaseModel):
    company: str
    title: str
    source: str
    posting_url: HttpUrl

    location: str | None = None
    remote_status: str | None = None
    salary: str | None = None
    date_posted: date | None = None
    description: str | None = None

    detected_stack: list[str] = Field(default_factory=list)
    match_score: int = 0