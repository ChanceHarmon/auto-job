from auto_job.models import Job
from auto_job.scoring import score_job
from auto_job.config import AppConfig


def build_test_config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "search": {
                "keywords": [
                    "backend engineer",
                    "software engineer",
                    "python developer",
                ],
                "remote_only": True,
                "recency_days": 7,
            },
            "filters": {
                "excluded_keywords": [
                    "senior",
                    "staff",
                    "principal",
                ],
                "preferred_stack": [
                    "python",
                    "django",
                    "postgresql",
                ],
                "minimum_score": 40,
            },
            "sources": {
                "enabled": [],
            },
        }
    )


def test_excluded_keyword_returns_zero_score():
    app_config = build_test_config()

    job = Job(
        company="Example Co",
        title="Senior Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score == 0
    assert job.detected_stack == []
    assert "excluded keyword: senior" in job.match_reasons


def test_excluded_keyword_in_description_does_not_return_zero_score():
    app_config = build_test_config()

    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Work with senior engineers on Python APIs and PostgreSQL.",
    )

    score = score_job(job, app_config)

    assert score > 0
    assert "excluded keyword: senior" not in job.match_reasons


def test_onsite_job_returns_zero_when_remote_only_enabled():
    app_config = build_test_config()

    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="San Francisco",
        remote_status="onsite",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score == 0
    assert job.detected_stack == []
    assert "not remote" in job.match_reasons


def test_matching_remote_job_gets_positive_score():
    app_config = build_test_config()

    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score > 0
    assert "python" in job.detected_stack
    assert "preferred stack: python" in job.match_reasons
