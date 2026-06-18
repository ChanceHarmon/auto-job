from datetime import datetime
from pathlib import Path
from html import escape, unescape
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
    # Provider descriptions often arrive as HTML or escaped HTML. Reports need
    # readable text, so normalize tags/entities before snippet extraction.
    description = unescape(description)
    description = re.sub(r"<[^>]+>", " ", description)
    description = " ".join(description.split())

    return description


def extract_description_snippet(description: str) -> str:
    # Prefer useful sections before falling back to the start of the posting.
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
        # Long postings often start with company marketing copy. Starting from
        # Requirements/Responsibilities makes the email more actionable.
        start_index, _heading = min(heading_positions)
        snippet = description[start_index:start_index + DESCRIPTION_PREVIEW_LENGTH]
        return snippet + "..."

    return description[:DESCRIPTION_PREVIEW_LENGTH] + "..."


def build_text_report(jobs: list[Job], limit: int = 20) -> str:
    # Plain text remains useful as a local artifact and fallback email body.
    lines = []

    lines.append("=" * 50)
    lines.append("AUTO-JOB REPORT")
    lines.append("=" * 50)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"Showing: {min(len(jobs), limit)} of {len(jobs)} matches")
    lines.append("")

    for index, job in enumerate(jobs[:limit], start=1):
        status = "NEW" if job.is_new else "SEEN"
        lines.append("-" * 50)
        lines.append(
            f"{index}. [{status}] {job.match_score} | "
            f"{job.title} @ {job.company}"
        )
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


def build_html_report(jobs: list[Job], limit: int = 20) -> str:
    # The HTML email is intentionally self-contained. Inline CSS keeps styling
    # compatible with common email clients without introducing templates.
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    shown_count = min(len(jobs), limit)
    cards = []

    for index, job in enumerate(jobs[:limit], start=1):
        badge_text = "New" if job.is_new else "Seen"
        badge_color = "#166534" if job.is_new else "#475569"
        description = (
            extract_description_snippet(job.description)
            if job.description
            else ""
        )

        stack_html = ""
        if job.detected_stack:
            stack_html = (
                "<p class=\"meta\"><strong>Stack:</strong> "
                f"{escape(', '.join(job.detected_stack))}</p>"
            )

        reasons_html = ""
        if job.match_reasons:
            reasons_html = (
                "<p class=\"meta\"><strong>Why matched:</strong> "
                f"{escape(', '.join(job.match_reasons))}</p>"
            )

        description_html = ""
        if description:
            description_html = (
                "<p class=\"description\">"
                f"{escape(description)}"
                "</p>"
            )

        cards.append(
            f"""
            <article class="job-card">
              <div class="job-heading">
                <span class="rank">#{index}</span>
                <span class="badge" style="background:{badge_color};">{badge_text}</span>
                <span class="score">{job.match_score}</span>
              </div>
              <h2>{escape(job.title)} <span>@ {escape(job.company)}</span></h2>
              <p class="meta">
                {escape(job.source)}
                &nbsp;|&nbsp;
                {escape(job.location or "Unknown location")}
                &nbsp;|&nbsp;
                {escape(job.remote_status or "Unknown remote status")}
              </p>
              {stack_html}
              {reasons_html}
              {description_html}
              <p><a class="apply" href="{escape(str(job.posting_url))}">Open posting</a></p>
            </article>
            """
        )

    return f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          body {{
            margin: 0;
            padding: 24px;
            background: #f8fafc;
            color: #0f172a;
            font-family: Arial, Helvetica, sans-serif;
            font-size: 17px;
            line-height: 1.55;
          }}
          .container {{
            max-width: 900px;
            margin: 0 auto;
          }}
          .header {{
            margin-bottom: 24px;
          }}
          h1 {{
            margin: 0 0 8px;
            font-size: 30px;
          }}
          .summary {{
            margin: 0;
            color: #475569;
            font-size: 16px;
          }}
          .job-card {{
            background: #ffffff;
            border: 1px solid #dbe3ee;
            border-radius: 8px;
            padding: 18px 20px;
            margin: 0 0 16px;
          }}
          .job-heading {{
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 8px;
          }}
          .rank,
          .score {{
            color: #475569;
            font-size: 15px;
            font-weight: 700;
          }}
          .badge {{
            border-radius: 999px;
            color: #ffffff;
            display: inline-block;
            font-size: 13px;
            font-weight: 700;
            letter-spacing: 0.02em;
            padding: 3px 9px;
            text-transform: uppercase;
          }}
          h2 {{
            margin: 0 0 8px;
            font-size: 22px;
            line-height: 1.3;
          }}
          h2 span {{
            color: #475569;
            font-weight: 600;
          }}
          .meta {{
            margin: 6px 0;
            color: #334155;
            font-size: 15px;
          }}
          .description {{
            color: #1e293b;
            margin: 12px 0;
          }}
          .apply {{
            color: #0f766e;
            font-weight: 700;
          }}
        </style>
      </head>
      <body>
        <main class="container">
          <section class="header">
            <h1>Auto-Job Report</h1>
            <p class="summary">
              Generated {generated_at}. Showing {shown_count} of {len(jobs)} matches.
            </p>
          </section>
          {''.join(cards)}
        </main>
      </body>
    </html>
    """


def save_text_report(report: str, output_dir: str = "reports") -> Path:
    # Saved reports stay text-based because they are easy to diff, search, and
    # open from the terminal. The styled version is only used for email.
    reports_dir = Path(output_dir)
    reports_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    report_path = reports_dir / f"auto-job-report-{timestamp}.txt"

    report_path.write_text(report, encoding="utf-8")

    return report_path
