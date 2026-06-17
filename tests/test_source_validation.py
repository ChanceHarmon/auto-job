import httpx

from auto_job.config import GreenhouseBoardConfig
from auto_job.source_validation import validate_greenhouse_board


def test_validate_greenhouse_board_returns_ok_with_job_count(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "jobs": [
                    {
                        "title": "Backend Engineer",
                    }
                ]
            }

    monkeypatch.setattr(
        "auto_job.source_validation.httpx.get",
        lambda url, timeout=10: FakeResponse(),
    )

    result = validate_greenhouse_board(
        GreenhouseBoardConfig(
            company="Example Co",
            board_token="example",
        )
    )

    assert result.provider == "greenhouse"
    assert result.status == "ok"
    assert result.job_count == 1


def test_validate_greenhouse_board_returns_error_for_http_error(monkeypatch):
    class FakeResponse:
        status_code = 404

        def raise_for_status(self):
            request = httpx.Request("GET", "https://example.com")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("not found", request=request, response=response)

    monkeypatch.setattr(
        "auto_job.source_validation.httpx.get",
        lambda url, timeout=10: FakeResponse(),
    )

    result = validate_greenhouse_board(
        GreenhouseBoardConfig(
            company="Example Co",
            board_token="example",
        )
    )

    assert result.provider == "greenhouse"
    assert result.status == "error"
    assert result.message == "HTTP 404"
