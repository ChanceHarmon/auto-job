from auto_job.config import AppConfig
from auto_job.sources.rss import RSSSource


def test_rss_source_keeps_summary_html_and_clean_text(monkeypatch):
    class FakeFeed:
        entries = [
            {
                "title": "Example Co: Backend Engineer",
                "link": "https://example.com/jobs/1",
                "summary": "<p>Build <strong>Python</strong> APIs.</p>",
            }
        ]

    config = AppConfig.model_validate(
        {
            "search": {},
            "filters": {},
            "sources": {
                "rss_feeds": [
                    {
                        "name": "Example Feed",
                        "url": "https://example.com/feed.xml",
                    }
                ]
            },
        }
    )

    monkeypatch.setattr(
        "auto_job.sources.rss.feedparser.parse",
        lambda url: FakeFeed(),
    )

    jobs = RSSSource(config).fetch_jobs()

    assert len(jobs) == 1
    assert jobs[0].company == "Example Co"
    assert jobs[0].title == "Backend Engineer"
    assert jobs[0].description == "Build Python APIs."
    assert jobs[0].description_html == "<p>Build <strong>Python</strong> APIs.</p>"
