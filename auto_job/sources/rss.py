import feedparser
from datetime import date

from auto_job.models import Job
from auto_job.sources.base import JobSource


def parse_rss_entry_date(entry) -> date | None:
    """Parse a date from common RSS/Atom date fields."""

    parsed_date = entry.get("published_parsed") or entry.get("updated_parsed")

    if not parsed_date:
        return None

    return date(
        parsed_date.tm_year,
        parsed_date.tm_mon,
        parsed_date.tm_mday,
    )


class RSSSource(JobSource):
    """Fetch jobs from configured RSS/Atom feeds."""

    name = "rss"

    def fetch_jobs(self) -> list[Job]:
        jobs: list[Job] = []

        for feed_config in self.config.sources.rss_feeds:
            feed = feedparser.parse(feed_config.url)

            for entry in feed.entries:
                try:
                    raw_title = entry.get("title", "Unknown")

                    if ":" in raw_title:
                        # Some feeds publish titles as "Company: Role"; split
                        # that into separate normalized fields when available.
                        company, title = raw_title.split(":", 1)
                        company = company.strip()
                        title = title.strip()
                    else:
                        company = feed_config.name
                        title = raw_title

                    job = Job(
                        company=company,
                        title=title,
                        source=f"rss:{feed_config.name}",
                        posting_url=entry.get("link"),
                        location="Remote",
                        remote_status="remote",
                        date_posted=parse_rss_entry_date(entry),
                        description=entry.get("summary", ""),
                    )

                    jobs.append(job)

                except Exception as error:
                    print(f"Failed to parse RSS job: {error}")

        return jobs
