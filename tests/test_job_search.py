# Tests for search diagnostics, filtering, and source match counts.

from auto_job.config import AppConfig
from auto_job.job_search import score_and_filter_jobs
from auto_job.models import Job


def build_test_config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "search": {
                "keywords": [
                    "backend engineer",
                ],
                "locations": [
                    "united states",
                    "canada",
                ],
                "remote_only": True,
            },
            "filters": {
                "minimum_score": 40,
                "excluded_keywords": [],
                "preferred_stack": [
                    "python",
                ],
            },
            "sources": {},
        }
    )


def test_score_and_filter_jobs_returns_diagnostics():
    jobs = [
        Job(
            company="Example Co",
            title="Backend Engineer",
            source="greenhouse",
            posting_url="https://example.com/jobs/1",
            location="United States Remote",
            remote_status="remote",
            description="Python APIs",
        ),
        Job(
            company="Office Co",
            title="Backend Engineer",
            source="greenhouse",
            posting_url="https://example.com/jobs/2",
            location="New York",
            remote_status="onsite",
            description="Python APIs",
        ),
        Job(
            company="Low Score Co",
            title="Operations Associate",
            source="rss:Example Feed",
            posting_url="https://example.com/jobs/3",
            location="United States",
            remote_status="remote",
            description="",
        ),
        Job(
            company="Outside Location Co",
            title="Backend Engineer",
            source="ashby",
            posting_url="https://example.com/jobs/4",
            location="Portugal Remote",
            remote_status="remote",
            description="Python APIs",
        ),
    ]

    matched_jobs, source_match_counts, filter_counts = score_and_filter_jobs(
        jobs,
        build_test_config(),
    )

    assert len(matched_jobs) == 1
    assert source_match_counts == {
        "greenhouse": 1,
    }
    assert filter_counts == {
        "not remote": 1,
        "outside allowed locations": 1,
        "below minimum score": 1,
    }
