from auto_job.sources.ashby import (
    build_ashby_posting_url,
    get_remote_status,
    parse_ashby_jobs,
)


def test_parse_ashby_jobs_extracts_job_data():
    html = '''
    "id":"123e4567-e89b-12d3-a456-426614174000",
    "title":"Software Engineer",
    "locationName":"Remote",
    "workplaceType":"Remote",
    "publishedDate":"2026-05-15"
    '''

    jobs = parse_ashby_jobs(html)

    assert len(jobs) == 1
    assert jobs[0][0] == "123e4567-e89b-12d3-a456-426614174000"
    assert jobs[0][1] == "Software Engineer"
    assert jobs[0][2] == "Remote"
    assert jobs[0][3] == "Remote"
    assert jobs[0][4] == "2026-05-15"


def test_get_remote_status_maps_remote_to_remote():
    assert get_remote_status("Remote") == "remote"


def test_get_remote_status_maps_hybrid_to_onsite():
    assert get_remote_status("Hybrid") == "onsite"


def test_build_ashby_posting_url():
    url = build_ashby_posting_url(
        "sentry",
        "123e4567-e89b-12d3-a456-426614174000",
    )

    assert url == "https://jobs.ashbyhq.com/sentry/123e4567-e89b-12d3-a456-426614174000"