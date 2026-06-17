from datetime import datetime
from pathlib import Path
from html import unescape
import re

from auto_job.models import Job

DESCRIPTION_PREVIEW_LENGTH = 2000
DESCRIPTION_SECTION_HEADINGS = [
    "requirements",
    "qualifications",
    "responsibilities",
    "what you'll do",
    "what you will do",
    "about you",
]


def clean_description(description: str) -> str:
    """Convert HTML-ish job descriptions into readable plain text."""

    description = unescape(description)
    description = re.sub(r"<[^>]+>", " ", description)
    description = " ".join(description.split())

    return description


def extract_description_snippet(description: str) -> str:
    description = clean_description(description)

    if len(description) <= DESCRIPTION_PREVIEW_LENGTH:
        return description

    lower_description = description.lower()
    heading_positions = [
        (lower_description.find(heading), heading)
        for heading in DESCRIPTION_SECTION_HEADINGS
        if lower_description.find(heading) != -1
    ]

    if heading_positions:
        start_index, _heading = min(heading_positions)
        snippet = description[start_index:start_index + DESCRIPTION_PREVIEW_LENGTH]
        return snippet + "..."

    return description[:DESCRIPTION_PREVIEW_LENGTH] + "..."


def build_text_report(jobs: list[Job], limit: int = 20) -> str:
    lines = []

    lines.append("=" * 50)
    lines.append("AUTO-JOB REPORT")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Showing: {min(len(jobs), limit)} of {len(jobs)} matches")
    lines.append("")

    for index, job in enumerate(jobs[:limit], start=1):
        lines.append("-" * 50)
        lines.append(f"{index}. {job.match_score} | {job.title} @ {job.company}")
        lines.append(f"Source: {job.source}")

        if job.location:
            lines.append(f"Location: {job.location}")

        if job.remote_status:
            lines.append(f"Remote: {job.remote_status}")

        if job.date_posted:
            lines.append(f"Date posted: {job.date_posted}")
        else:
            lines.append("Date posted: unknown")

        if job.detected_stack:
            lines.append(f"Detected stack: {', '.join(job.detected_stack)}")

        if job.match_reasons:
            lines.append(f"Match reasons: {', '.join(job.match_reasons)}")

        if job.description:
            lines.append(f"Description: {extract_description_snippet(job.description)}")

        lines.append(f"Apply: {job.posting_url}")
        lines.append("")

    return "\n".join(lines)


def save_text_report(report: str, output_dir: str = "reports") -> Path:
    """Save a text report and return the file path."""
    reports_dir = Path(output_dir)
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = reports_dir / f"auto-job-report-{timestamp}.txt"

    report_path.write_text(report, encoding="utf-8")

    return report_path
