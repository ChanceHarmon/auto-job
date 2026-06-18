# Tests for Lever date parsing, description building, and API error handling.

from datetime import date

from auto_job.config import AppConfig
from auto_job.sources.lever import (
    LeverSource,
    build_lever_description,
    detect_lever_remote_status,
    normalize_lever_posting,
    parse_lever_date,
)


def test_parse_lever_date_returns_date():
    result = parse_lever_date(1781557489000)

    assert result == date(2026, 6, 15)


def test_detect_lever_remote_status():
    assert detect_lever_remote_status("Remote") == "remote"
    assert detect_lever_remote_status("New York, NY") == "onsite"
    assert detect_lever_remote_status(None) == "unknown"


def test_build_lever_description_includes_content_sections():
    description = build_lever_description(
        {
            "content": {
                "description": "Build backend systems.",
                "lists": [
                    {
                        "text": "What you will do",
                        "content": "Work with Python and PostgreSQL.",
                    }
                ],
                "closing": "Equal opportunity employer.",
            }
        }
    )

    assert "Build backend systems." in description
    assert "What you will do" in description
    assert "Work with Python and PostgreSQL." in description
    assert "Equal opportunity employer." in description


def test_normalize_lever_posting_returns_job():
    job = normalize_lever_posting(
        "Example Co",
        {
            "text": "Backend Engineer",
            "hostedUrl": "https://jobs.lever.co/example/backend-engineer",
            "createdAt": 1781557489000,
            "categories": {
                "location": "Remote",
            },
            "content": {
                "description": "Build APIs.",
            },
        },
    )

    assert job.company == "Example Co"
    assert job.title == "Backend Engineer"
    assert str(job.posting_url) == "https://jobs.lever.co/example/backend-engineer"
    assert job.location == "Remote"
    assert job.remote_status == "remote"
    assert job.date_posted == date(2026, 6, 15)
    assert job.description == "Build APIs."


def test_lever_source_skips_404_companies(monkeypatch):
    class FakeResponse:
        status_code = 404

        def raise_for_status(self):
            import httpx

            request = httpx.Request("GET", "https://api.lever.co/v0/postings/missing")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("not found", request=request, response=response)

    def fake_get(url, timeout=10):
        return FakeResponse()

    config = AppConfig.model_validate(
        {
            "search": {},
            "filters": {},
            "sources": {
                "lever_companies": [
                    {
                        "company": "Missing Co",
                        "company_slug": "missing",
                    }
                ]
            },
        }
    )

    monkeypatch.setattr("auto_job.sources.lever.httpx.get", fake_get)

    jobs = LeverSource(config).fetch_jobs()

    assert jobs == []
