from datetime import date

from pydantic import BaseModel, HttpUrl, Field


class Job(BaseModel):
    """Normalized internal job shape shared by every source adapter.

    External providers all return different fields and naming conventions. The
    rest of the application only works with this model so scoring, storage, and
    reporting do not need provider-specific conditionals.
    """

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
    match_reasons: list[str] = Field(default_factory=list)
    match_score: int = 0
    is_new: bool = False
