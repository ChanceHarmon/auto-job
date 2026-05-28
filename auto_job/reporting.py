from datetime import datetime
from pathlib import Path
from html import unescape
import re

from auto_job.models import Job

DESCRIPTION_PREVIEW_LENGTH = 500


def clean_description(description: str) -> str:
    """Convert HTML-ish job descriptions into readable plain text."""

    description = unescape(description)
    description = re.sub(r"<[^>]+>", " ", description)
    description = " ".join(description.split())

    return description


def build_text_report(jobs: list[Job], limit: int = 10) -> str:
    lines = []

    lines.append("=" * 50)
    lines.append("AUTO-JOB REPORT")
    lines.append("=" * 50)
    lines.append("")

    for job in jobs[:limit]:
        lines.append(f"{job.match_score} | {job.title} @ {job.company}")
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
            description = clean_description(job.description)

            if len(description) > DESCRIPTION_PREVIEW_LENGTH:
                description = description[:DESCRIPTION_PREVIEW_LENGTH] + "..."

            lines.append(f"Description: {description}")

        lines.append(str(job.posting_url))
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