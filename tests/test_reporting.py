from auto_job.models import Job
from auto_job.reporting import (
    DESCRIPTION_PREVIEW_LENGTH,
    build_text_report,
    extract_description_snippet,
)


def build_job(index: int, description: str = "Python APIs") -> Job:
    return Job(
        company=f"Example {index}",
        title="Backend Engineer",
        source="test",
        posting_url=f"https://example.com/jobs/{index}",
        location="Remote",
        remote_status="remote",
        description=description,
        match_score=100 - index,
        match_reasons=["remote"],
    )


def test_text_report_defaults_to_twenty_jobs():
    jobs = [build_job(index) for index in range(25)]

    report = build_text_report(jobs)

    assert "Showing: 20 of 25 matches" in report
    assert "20. 81 | Backend Engineer @ Example 19" in report
    assert "21. 80 | Backend Engineer @ Example 20" not in report


def test_text_report_uses_longer_description_preview():
    description = "x" * (DESCRIPTION_PREVIEW_LENGTH + 100)

    report = build_text_report([build_job(1, description=description)])

    assert f"Description: {'x' * DESCRIPTION_PREVIEW_LENGTH}..." in report
    assert f"{'x' * (DESCRIPTION_PREVIEW_LENGTH + 1)}" not in report
    assert "Apply: https://example.com/jobs/1" in report


def test_description_snippet_prefers_requirements_section():
    description = (
        f"{'intro ' * 600}"
        "Requirements Python APIs PostgreSQL production systems"
    )

    snippet = extract_description_snippet(description)

    assert snippet.startswith("Requirements Python APIs")
    assert "intro intro intro" not in snippet
