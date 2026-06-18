# Tests for Ashby parsing, description fetching, and source normalization.

from auto_job.sources.ashby import (
    AshbySource,
    build_ashby_posting_url,
    fetch_ashby_descriptions,
    get_remote_status,
    parse_ashby_description,
    parse_ashby_jobs,
)
from auto_job.config import AppConfig


def test_parse_ashby_jobs_extracts_job_data():
    html = '''
    "id":"123e4567-e89b-12d3-a456-426614174000",
    "title":"Software Engineer",
    "locationName":"Remote",
    "workplaceType":"Remote",
    "publishedDate":"2026-05-15"
    '''

    jobs = parse_ashby_jobs(html)

    assert len(jobs) == 1
    assert jobs[0][0] == "123e4567-e89b-12d3-a456-426614174000"
    assert jobs[0][1] == "Software Engineer"
    assert jobs[0][2] == "Remote"
    assert jobs[0][3] == "Remote"
    assert jobs[0][4] == "2026-05-15"


def test_parse_ashby_jobs_returns_empty_for_large_partial_match():
    html = (
        '"id":"123e4567-e89b-12d3-a456-426614174000"'
        + (" filler " * 20000)
    )

    jobs = parse_ashby_jobs(html)

    assert jobs == []


def test_get_remote_status_maps_remote_to_remote():
    assert get_remote_status("Remote") == "remote"


def test_parse_ashby_description_extracts_json_ld_description():
    html = """
    <html>
        <head>
            <script type="application/ld+json">
                {
                    "@context": "https://schema.org/",
                    "@type": "JobPosting",
                    "title": "Product Engineer",
                    "description": "<p>Build Python APIs with PostgreSQL.</p>"
                }
            </script>
        </head>
    </html>
    """

    description = parse_ashby_description(html)

    assert description == "<p>Build Python APIs with PostgreSQL.</p>"


def test_parse_ashby_description_falls_back_to_meta_description():
    html = """
    <html>
        <head>
            <meta name="description" content="Build Python APIs with PostgreSQL." />
        </head>
    </html>
    """

    description = parse_ashby_description(html)

    assert description == "Build Python APIs with PostgreSQL."


def test_ashby_source_fetches_job_descriptions(monkeypatch):
    board_html = '''
    "id":"123e4567-e89b-12d3-a456-426614174000",
    "title":"Software Engineer",
    "locationName":"Remote",
    "workplaceType":"Remote",
    "publishedDate":"2026-05-15"
    '''
    detail_html = """
    <script type="application/ld+json">
        {
            "@context": "https://schema.org/",
            "@type": "JobPosting",
            "description": "<p>Python APIs and PostgreSQL.</p>"
        }
    </script>
    """

    class FakeResponse:
        def __init__(self, text):
            self.text = text

        def raise_for_status(self):
            pass

    def fake_get(url, timeout=10):
        if url == "https://jobs.ashbyhq.com/example":
            return FakeResponse(board_html)

        return FakeResponse(detail_html)

    config = AppConfig.model_validate(
        {
            "search": {},
            "filters": {},
            "sources": {
                "ashby_companies": [
                    {
                        "company": "Example",
                        "company_slug": "example",
                    }
                ]
            },
        }
    )

    monkeypatch.setattr("auto_job.sources.ashby.httpx.get", fake_get)

    jobs = AshbySource(config).fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].description == "<p>Python APIs and PostgreSQL.</p>"


def test_fetch_ashby_descriptions_returns_descriptions_by_url(monkeypatch):
    posting_urls = [
        "https://jobs.ashbyhq.com/example/1",
        "https://jobs.ashbyhq.com/example/2",
    ]

    monkeypatch.setattr(
        "auto_job.sources.ashby.fetch_ashby_description",
        lambda posting_url: f"description for {posting_url}",
    )

    descriptions = fetch_ashby_descriptions(posting_urls)

    assert descriptions == {
        "https://jobs.ashbyhq.com/example/1": "description for https://jobs.ashbyhq.com/example/1",
        "https://jobs.ashbyhq.com/example/2": "description for https://jobs.ashbyhq.com/example/2",
    }


def test_get_remote_status_maps_hybrid_to_onsite():
    assert get_remote_status("Hybrid") == "onsite"


def test_build_ashby_posting_url():
    url = build_ashby_posting_url(
        "sentry",
        "123e4567-e89b-12d3-a456-426614174000",
    )

    assert url == "https://jobs.ashbyhq.com/sentry/123e4567-e89b-12d3-a456-426614174000"
