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
    board_token: str | None = None


def detect_ats_provider(url: str) -> AtsDetectionResult | None:
    """Detect ATS provider from careers page HTML."""
    response = httpx.get(url, follow_redirects=True, timeout=10)
    html = response.text.lower()

    for provider, pattern in ATS_PATTERNS.items():
        if pattern in html:
            ats_url = extract_first_matching_url(html, pattern)

            board_token = None

            if provider == "greenhouse" and ats_url:
                board_token = extract_greenhouse_board_token(ats_url)

            return AtsDetectionResult(
                provider=provider,
                matched_pattern=pattern,
                final_url=str(response.url),
                ats_url=ats_url,
                board_token=board_token,
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