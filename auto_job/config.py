from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class SearchConfig(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    remote_only: bool = True
    salary_min: int | None = None
    recency_days: int = 7

class FilterConfig(BaseModel):
    excluded_keywords: list[str] = []
    preferred_stack: list[str] = []
    minimum_score: int = 40

class SourceConfig(BaseModel):
    enabled: list[str] = Field(default_factory=list)
    rss_feeds: list[RSSFeedConfig] = Field(default_factory=list)
    greenhouse_boards: list[GreenhouseBoardConfig] = Field(default_factory=list)
    lever_companies: list[LeverCompanyConfig] = Field(default_factory=list)
    ashby_companies: list[AshbyCompanyConfig] = Field(default_factory=list)

class AppConfig(BaseModel):
    search: SearchConfig
    filters: FilterConfig
    sources: SourceConfig

class RSSFeedConfig(BaseModel):
    name: str
    url: str

class GreenhouseBoardConfig(BaseModel):
    company: str
    board_token: str

class LeverCompanyConfig(BaseModel):
    company: str
    company_slug: str

class AshbyCompanyConfig(BaseModel):
    company: str
    company_slug: str


def load_config(path: str = "config.yaml") -> AppConfig:
    config_path = Path(path)

    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    return AppConfig.model_validate(raw_config)