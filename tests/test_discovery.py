from auto_job.ats import AtsDetectionResult
from auto_job.discovery import dedupe_discovery_results, get_discovery_urls_from_jobs
from auto_job.models import Job


def test_dedupe_discovery_results_removes_duplicate_provider_and_slug():
    results = [
        AtsDetectionResult("ashby", "jobs.ashbyhq.com", "https://jobs.ashbyhq.com/sentry", "https://jobs.ashbyhq.com/sentry", "sentry"),
        AtsDetectionResult("ashby", "jobs.ashbyhq.com", "https://jobs.ashbyhq.com/sentry", "https://jobs.ashbyhq.com/sentry", "sentry"),
    ]

    unique_results = dedupe_discovery_results(results)

    assert len(unique_results) == 1
    assert unique_results[0].provider == "ashby"
    assert unique_results[0].company_slug == "sentry"


def test_get_discovery_urls_from_jobs_returns_posting_urls():
    jobs = [
        Job(
            company="ExampleCo",
            title="Software Engineer",
            source="rss",
            posting_url="https://example.com/jobs/1",
            location="Remote",
            remote_status="remote",
            description="",
        ),
        Job(
            company="AnotherCo",
            title="Backend Engineer",
            source="rss",
            posting_url="https://example.com/jobs/2",
            location="Remote",
            remote_status="remote",
            description="",
        ),
    ]

    urls = get_discovery_urls_from_jobs(jobs)

    assert urls == [
        "https://example.com/jobs/1",
        "https://example.com/jobs/2",
    ]