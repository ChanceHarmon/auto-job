# Tests for the larger source maintenance command that can discover, write,
# and prune company job boards from a configured company universe.

import yaml

from auto_job.company_source_discovery import (
    discover_company_sources,
    load_company_candidates,
    slugify_company_name,
)
from auto_job.config import AppConfig
from auto_job.source_validation import SourceValidationResult


def build_app_config(config_data: dict) -> AppConfig:
    return AppConfig.model_validate(config_data)


def write_yaml(path, data):
    with open(path, "w", encoding="utf-8") as file:
        yaml.safe_dump(data, file, sort_keys=False)


def read_yaml(path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def base_config() -> dict:
    return {
        "search": {"keywords": [], "locations": []},
        "filters": {},
        "sources": {
            "enabled": ["greenhouse", "lever", "ashby"],
            "rss_feeds": [],
            "greenhouse_boards": [],
            "lever_companies": [],
            "ashby_companies": [],
        },
        "email": {"enabled": False},
    }


def test_slugify_company_name_removes_spaces_and_punctuation():
    assert slugify_company_name("Acme AI, Inc.") == "acmeaiinc"


def test_load_company_candidates_uses_explicit_or_generated_slugs(tmp_path):
    company_file = tmp_path / "companies.yaml"
    write_yaml(
        company_file,
        {
            "companies": [
                {
                    "name": "Acme AI",
                    "industries": ["technology"],
                    "slugs": ["acme", "acmeai"],
                },
                {
                    "name": "North Star Learning",
                    "industries": ["education", "edtech"],
                },
            ]
        },
    )

    candidates = load_company_candidates(company_file)

    assert candidates[0].name == "Acme AI"
    assert candidates[0].slugs == ["acme", "acmeai"]
    assert candidates[1].slugs == ["northstarlearning"]


def test_discover_company_sources_dry_run_does_not_write(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    company_file = tmp_path / "companies.yaml"
    config_data = base_config()
    write_yaml(config_path, config_data)
    write_yaml(
        company_file,
        {"companies": [{"name": "Acme AI", "slugs": ["acme"]}]},
    )

    monkeypatch.setattr(
        "auto_job.company_source_discovery.validate_candidate_provider",
        lambda provider, company, slug: SourceValidationResult(
            provider=provider,
            company=company,
            identifier=slug,
            status="ok",
            job_count=3,
        ),
    )
    monkeypatch.setattr(
        "auto_job.company_source_discovery.validate_sources",
        lambda app_config: [],
    )

    result = discover_company_sources(
        build_app_config(config_data),
        config_path=str(config_path),
        company_file=company_file,
        providers=["greenhouse"],
        write=False,
    )

    updated_config = read_yaml(config_path)

    assert len(result.discoveries) == 1
    assert result.added_count == 0
    assert updated_config["sources"]["greenhouse_boards"] == []


def test_discover_company_sources_writes_verified_new_sources(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    company_file = tmp_path / "companies.yaml"
    config_data = base_config()
    write_yaml(config_path, config_data)
    write_yaml(
        company_file,
        {"companies": [{"name": "Acme AI", "slugs": ["acme"]}]},
    )

    monkeypatch.setattr(
        "auto_job.company_source_discovery.validate_candidate_provider",
        lambda provider, company, slug: SourceValidationResult(
            provider=provider,
            company=company,
            identifier=slug,
            status="ok",
            job_count=7,
        ),
    )
    monkeypatch.setattr(
        "auto_job.company_source_discovery.validate_sources",
        lambda app_config: [],
    )

    result = discover_company_sources(
        build_app_config(config_data),
        config_path=str(config_path),
        company_file=company_file,
        providers=["lever"],
        write=True,
    )

    updated_config = read_yaml(config_path)
    companies = updated_config["sources"]["lever_companies"]

    assert result.added_count == 1
    assert companies == [
        {
            "company": "Acme AI",
            "company_slug": "acme",
            "discovered_via": "company_universe",
        }
    ]


def test_discover_company_sources_prunes_only_hard_404s(monkeypatch, tmp_path):
    config_path = tmp_path / "config.yaml"
    company_file = tmp_path / "companies.yaml"
    config_data = base_config()
    config_data["sources"]["greenhouse_boards"] = [
        {"company": "Broken Co", "board_token": "broken"},
        {"company": "Empty Co", "board_token": "empty"},
    ]
    write_yaml(config_path, config_data)
    write_yaml(company_file, {"companies": []})

    monkeypatch.setattr(
        "auto_job.company_source_discovery.validate_sources",
        lambda app_config: [
            SourceValidationResult(
                provider="greenhouse",
                company="Broken Co",
                identifier="broken",
                status="error",
                message="HTTP 404",
            ),
            SourceValidationResult(
                provider="greenhouse",
                company="Empty Co",
                identifier="empty",
                status="empty",
            ),
        ],
    )

    result = discover_company_sources(
        build_app_config(config_data),
        config_path=str(config_path),
        company_file=company_file,
        providers=["greenhouse"],
        write=True,
        prune_stale=True,
    )

    updated_config = read_yaml(config_path)
    boards = updated_config["sources"]["greenhouse_boards"]

    assert result.pruned_count == 1
    assert boards == [{"company": "Empty Co", "board_token": "empty"}]
