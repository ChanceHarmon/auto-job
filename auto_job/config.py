from pathlib import Path

import yaml
from pydantic import BaseModel


class SearchConfig(BaseModel):
    keywords: list[str]
    remote_only: bool = True

class FilterConfig(BaseModel):
    excluded_keywords: list[str] = []
    preferred_stack: list[str] = []
    minimum_score: int = 40

class SourceConfig(BaseModel):
    enabled: list[str]


class AppConfig(BaseModel):
    search: SearchConfig
    filters: FilterConfig
    sources: SourceConfig


def load_config(path: str = "config.yaml") -> AppConfig:
    config_path = Path(path)

    with config_path.open("r", encoding="utf-8") as file:
        raw_config = yaml.safe_load(file)

    return AppConfig.model_validate(raw_config)