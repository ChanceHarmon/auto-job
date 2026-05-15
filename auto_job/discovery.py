from auto_job.ats import detect_ats_provider, AtsDetectionResult
from auto_job.models import Job


def discover_ats_from_job_urls(
    urls: list[str],
) -> list[AtsDetectionResult]:
    """Detect ATS providers from a list of job/careers URLs."""

    results = []

    for url in urls:
        try:
            result = detect_ats_provider(url)

            if result:
                results.append(result)

        except Exception as error:
            print(f"Error detecting ATS for {url}: {error}")

    return dedupe_discovery_results(results)


def dedupe_discovery_results(
    results: list[AtsDetectionResult],
) -> list[AtsDetectionResult]:
    """Remove duplicate ATS discoveries."""

    seen = set()
    unique_results = []

    for result in results:
        key = (result.provider, result.company_slug)

        if key in seen:
            continue

        seen.add(key)
        unique_results.append(result)

    return unique_results


def get_discovery_urls_from_jobs(jobs: list[Job]) -> list[str]:
    """Extract usable URLs from normalized jobs for ATS discovery."""

    urls = []

    for job in jobs:
        if job.posting_url:
            urls.append(str(job.posting_url))

    return urls