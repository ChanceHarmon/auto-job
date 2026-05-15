from auto_job.models import Job
from auto_job.scoring import score_job
from auto_job.config import load_config


def test_excluded_keyword_returns_zero_score():
    app_config = load_config()

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


def test_onsite_job_returns_zero_when_remote_only_enabled():
    app_config = load_config()

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


def test_matching_remote_job_gets_positive_score():
    app_config = load_config()

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