from datetime import datetime
from pathlib import Path

from auto_job.models import Job


def build_text_report(jobs: list[Job], limit: int = 10) -> str:
    lines = []

    lines.append("auto-job report")
    lines.append("")
    lines.append(f"Showing top {min(len(jobs), limit)} of {len(jobs)} matched jobs")
    lines.append("")

    for job in jobs[:limit]:
        lines.append(f"{job.match_score} | {job.title} @ {job.company}")
        lines.append(f"{job.source} | {job.location or 'Unknown location'} | {job.remote_status or 'Unknown remote status'}")
        lines.append(str(job.posting_url) if job.posting_url else "No URL")
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