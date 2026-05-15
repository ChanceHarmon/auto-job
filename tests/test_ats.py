from auto_job.ats import extract_first_matching_url
from auto_job.ats import extract_greenhouse_board_token
from auto_job.ats import extract_lever_company_slug
from auto_job.ats import extract_ashby_company_slug
from auto_job.ats import detect_ats_from_text


def test_extracts_greenhouse_url():
    html = """
    <html>
        <body>
            <a href="https://boards.greenhouse.io/vercel">
                Jobs
            </a>
        </body>
    </html>
    """

    result = extract_first_matching_url(
        html,
        "boards.greenhouse.io",
    )

    assert result == "https://boards.greenhouse.io/vercel"


def test_extracts_greenhouse_board_token():
    url = "https://boards.greenhouse.io/vercel"

    result = extract_greenhouse_board_token(url)

    assert result == "vercel"


def test_extracts_lever_company_slug():
    url = "https://jobs.lever.co/example-company"

    result = extract_lever_company_slug(url)

    assert result == "example-company"


def test_extracts_ashby_company_slug():
    url = "https://jobs.ashbyhq.com/sentry"

    result = extract_ashby_company_slug(url)

    assert result == "sentry"


def test_detect_ats_from_text_detects_ashby():
    html = '<a href="https://jobs.ashbyhq.com/sentry">Jobs</a>'
    final_url = "https://sentry.io/careers"

    result = detect_ats_from_text(html, final_url)

    assert result is not None
    assert result.provider == "ashby"
    assert result.company_slug == "sentry"
    assert result.ats_url == "https://jobs.ashbyhq.com/sentry"


def test_detect_ats_from_text_detects_greenhouse():
    html = '<a href="https://boards.greenhouse.io/mozilla">Jobs</a>'
    final_url = "https://mozilla.org/careers"

    result = detect_ats_from_text(html, final_url)

    assert result is not None
    assert result.provider == "greenhouse"
    assert result.company_slug == "mozilla"
    assert result.ats_url == "https://boards.greenhouse.io/mozilla"