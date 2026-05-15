from auto_job.ats import extract_first_matching_url
from auto_job.ats import extract_greenhouse_board_token
from auto_job.ats import extract_lever_company_slug
from auto_job.ats import extract_ashby_company_slug


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