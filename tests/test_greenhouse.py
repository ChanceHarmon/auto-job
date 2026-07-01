from auto_job.config import AppConfig
from auto_job.sources.greenhouse import GreenhouseSource


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self.payload


def build_config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "search": {},
            "filters": {},
            "sources": {
                "enabled": ["greenhouse"],
                "greenhouse_boards": [
                    {
                        "company": "Example Co",
                        "board_token": "example",
                    }
                ],
            },
        }
    )


def test_greenhouse_source_keeps_html_and_clean_text(monkeypatch):
    payload = {
        "jobs": [
            {
                "title": "Backend Engineer",
                "absolute_url": "https://example.com/jobs/1",
                "location": {"name": "Remote"},
                "updated_at": "2026-06-01T12:00:00+00:00",
                "content": (
                    "<p>Build <strong>Python</strong> APIs.</p>"
                    "<ul><li>Own PostgreSQL services</li></ul>"
                ),
            }
        ]
    }

    monkeypatch.setattr(
        "auto_job.sources.greenhouse.httpx.get",
        lambda *args, **kwargs: FakeResponse(payload),
    )

    jobs = GreenhouseSource(build_config()).fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].description == "Build Python APIs. Own PostgreSQL services"
    assert "<strong>Python</strong>" in jobs[0].description_html
    assert "<li>Own PostgreSQL services</li>" in jobs[0].description_html
