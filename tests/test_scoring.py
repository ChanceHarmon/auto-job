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


def build_location_config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "search": {
                "keywords": [
                    "backend engineer",
                ],
                "locations": [
                    "remote",
                    "united states",
                    "canada",
                ],
                "remote_only": True,
                "recency_days": 7,
            },
            "filters": {
                "excluded_keywords": [],
                "preferred_stack": [
                    "python",
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


def test_senior_excluded_keyword_matches_sr_title_abbreviation():
    app_config = build_test_config()

    job = Job(
        company="Example Co",
        title="Sr. Software Engineer II",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score == 0
    assert "excluded keyword: senior" in job.match_reasons


def test_short_excluded_keyword_matches_title_token_only():
    app_config = build_test_config()
    app_config.filters.excluded_keywords = ["it"]

    matching_job = Job(
        company="Example Co",
        title="IT Systems Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )
    non_matching_job = Job(
        company="Example Co",
        title="Site Reliability Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    assert score_job(matching_job, app_config) == 0
    assert "excluded keyword: it" in matching_job.match_reasons
    assert score_job(non_matching_job, app_config) > 0


def test_machine_learning_title_can_be_excluded():
    app_config = build_test_config()
    app_config.filters.excluded_keywords = ["machine learning"]

    job = Job(
        company="Example Co",
        title="Machine Learning Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score == 0
    assert "excluded keyword: machine learning" in job.match_reasons


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


def test_remote_job_outside_allowed_locations_returns_zero_score():
    app_config = build_location_config()

    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Portugal Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score == 0
    assert "outside allowed locations" in job.match_reasons


def test_us_remote_job_matches_allowed_locations():
    app_config = build_location_config()

    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="US-Remote, Chicago, Seattle, San Francisco",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score > 0


def test_canada_remote_job_matches_allowed_locations():
    app_config = build_location_config()

    job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Toronto, CAN-Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    score = score_job(job, app_config)

    assert score > 0


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


def test_penalty_keyword_reduces_score_without_excluding_job():
    app_config = build_test_config()
    app_config.filters.penalty_keywords = ["intern"]

    normal_job = Job(
        company="Example Co",
        title="Backend Engineer",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )
    penalty_job = Job(
        company="Example Co",
        title="Backend Engineer Intern",
        source="test",
        posting_url="https://example.com/job",
        location="Remote",
        remote_status="remote",
        description="Python APIs PostgreSQL",
    )

    normal_score = score_job(normal_job, app_config)
    penalty_score = score_job(penalty_job, app_config)

    assert penalty_score == normal_score - 20
    assert penalty_score > 0
    assert "title penalty: intern" in penalty_job.match_reasons
