import httpx
from dataclasses import dataclass
import re


ATS_PATTERNS = {
    "greenhouse": "boards.greenhouse.io",
    "lever": "jobs.lever.co",
    "ashby": "jobs.ashbyhq.com",
}


def extract_first_matching_url(html: str, pattern: str) -> str | None:
    """Extract the first URL containing the matched ATS pattern."""
    url_pattern = rf"https?://[^\"'\s<>]*{re.escape(pattern)}[^\"'\s<>]*"
    match = re.search(url_pattern, html)

    if match:
        return match.group(0)

    return None


@dataclass
class AtsDetectionResult:
    provider: str
    matched_pattern: str
    final_url: str
    ats_url: str | None = None
    company_slug: str | None = None


def detect_ats_provider(url: str) -> AtsDetectionResult | None:
    """Detect ATS provider from careers page HTML."""
    response = httpx.get(url, follow_redirects=True, timeout=10)
    html = response.text.lower()
    final_url = str(response.url).lower()

    searchable_text = f"{final_url}\n{html}"

    for provider, pattern in ATS_PATTERNS.items():
        if pattern in searchable_text:
            ats_url = extract_first_matching_url(searchable_text, pattern)

            if ats_url is None and pattern in final_url:
                ats_url = str(response.url)

            company_slug = None

            if ats_url:
                if provider == "greenhouse":
                    company_slug = extract_greenhouse_board_token(ats_url)

                elif provider == "lever":
                    company_slug = extract_lever_company_slug(ats_url)

            return AtsDetectionResult(
                provider=provider,
                matched_pattern=pattern,
                final_url=str(response.url),
                ats_url=ats_url,
                company_slug=company_slug,
            )

    return None


def extract_greenhouse_board_token(url: str) -> str | None:
    """Extract Greenhouse board token from URL."""
    match = re.search(
        r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)",
        url,
    )

    if match:
        return match.group(1)

    return None

def extract_lever_company_slug(url: str) -> str | None:
    """Extract Lever company slug from URL."""
    match = re.search(
        r"jobs\.lever\.co/([a-zA-Z0-9_-]+)",
        url,
    )

    if match:
        return match.group(1)

    return None