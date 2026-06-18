# Tests for report formatting and useful job description snippets.

from auto_job.models import Job
from auto_job.reporting import (
    DESCRIPTION_PREVIEW_LENGTH,
    build_html_report,
    build_text_report,
    clean_description,
    extract_description_snippet,
    format_match_summary_text,
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
    assert "20. [SEEN] 81 | Backend Engineer @ Example 19" in report
    assert "21. [SEEN] 80 | Backend Engineer @ Example 20" not in report


def test_text_report_marks_new_and_seen_jobs():
    new_job = build_job(1)
    new_job.is_new = True
    seen_job = build_job(2)

    report = build_text_report([new_job, seen_job])

    assert "1. [NEW] 99 | Backend Engineer @ Example 1" in report
    assert "2. [SEEN] 98 | Backend Engineer @ Example 2" in report


def test_html_report_includes_styled_status_badges():
    new_job = build_job(1)
    new_job.is_new = True
    seen_job = build_job(2)

    report = build_html_report([new_job, seen_job])

    assert "<!doctype html>" in report
    assert ">New</span>" in report
    assert ">Seen</span>" in report
    assert "font-size: 17px" in report
    assert "Open posting" in report


def test_match_reasons_are_grouped_for_reports():
    lines = format_match_summary_text(
        [
            "keyword match: backend engineer",
            "keyword match: software engineer",
            "preferred stack: python",
            "preferred stack: sql",
            "remote",
        ]
    )

    assert lines == [
        "Keywords: backend engineer, software engineer",
        "Stack: python, sql",
        "Other: remote",
    ]


def test_html_report_groups_match_reasons():
    job = build_job(1)
    job.match_reasons = [
        "keyword match: backend engineer",
        "preferred stack: python",
        "remote",
    ]

    report = build_html_report([job])

    assert "<strong>Why matched</strong>" in report
    assert "<strong>Keywords:</strong> backend engineer" in report
    assert "<strong>Stack:</strong> python" in report
    assert "<strong>Other:</strong> remote" in report


def test_text_report_uses_longer_description_preview():
    description = "x" * (DESCRIPTION_PREVIEW_LENGTH + 100)

    report = build_text_report([build_job(1, description=description)])

    assert f"Description:\n{'x' * DESCRIPTION_PREVIEW_LENGTH}..." in report
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


def test_clean_description_removes_lingering_html_entities():
    description = "Build APIs &amp;amp; services &amp;nbsp; with Python&nbsp;and SQL"

    cleaned = clean_description(description)

    assert cleaned == "Build APIs and services with Python and SQL"
    assert "amp" not in cleaned
    assert "nbsp" not in cleaned


def test_html_report_breaks_description_into_sections():
    job = build_job(
        1,
        description=(
            "Responsibilities Build APIs and integrations "
            "Requirements Python and SQL "
            "Qualifications Production experience"
        ),
    )

    report = build_html_report([job])

    assert '<section class="description-section">' in report
    assert "<h3>Responsibilities</h3>" in report
    assert "<h3>Requirements</h3>" in report
    assert "<h3>Qualifications</h3>" in report
