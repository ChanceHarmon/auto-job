# Tests for RemoteOK normalization and API response handling.

from datetime import date

from auto_job.config import AppConfig
from auto_job.sources.remoteok import (
    RemoteOKSource,
    format_remoteok_salary,
    normalize_remoteok_job,
    parse_remoteok_date,
)


def test_parse_remoteok_date_returns_date():
    result = parse_remoteok_date("2026-06-15T21:04:49+00:00")

    assert result == date(2026, 6, 15)


def test_format_remoteok_salary_returns_range():
    salary = format_remoteok_salary(
        {
            "salary_min": 100000,
            "salary_max": 140000,
        }
    )

    assert salary == "$100,000 - $140,000"


def test_normalize_remoteok_job_includes_tags_in_description():
    job = normalize_remoteok_job(
        {
            "company": "Example Co",
            "position": "Backend Engineer",
            "url": "https://remoteok.com/remote-jobs/example",
            "location": "",
            "date": "2026-06-15T21:04:49+00:00",
            "salary_min": 100000,
            "salary_max": 140000,
            "description": "Build APIs.",
            "tags": [
                "python",
                "postgresql",
            ],
        }
    )

    assert job.company == "Example Co"
    assert job.title == "Backend Engineer"
    assert str(job.posting_url) == "https://remoteok.com/remote-jobs/example"
    assert job.location is None
    assert job.remote_status == "remote"
    assert job.salary == "$100,000 - $140,000"
    assert job.date_posted == date(2026, 6, 15)
    assert "Build APIs." in job.description
    assert "Tags: python, postgresql" in job.description


def test_remoteok_source_skips_metadata_row(monkeypatch):
    raw_payload = [
        {
            "last_updated": 1781636710,
        },
        {
            "company": "Example Co",
            "position": "Backend Engineer",
            "url": "https://remoteok.com/remote-jobs/example",
            "date": "2026-06-15T21:04:49+00:00",
            "description": "Build APIs.",
            "tags": [],
        },
    ]

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return raw_payload

    def fake_get(url, headers=None, timeout=10):
        return FakeResponse()

    config = AppConfig.model_validate(
        {
            "search": {},
            "filters": {},
            "sources": {},
        }
    )

    monkeypatch.setattr("auto_job.sources.remoteok.httpx.get", fake_get)

    jobs = RemoteOKSource(config).fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].company == "Example Co"
