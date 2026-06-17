import httpx

from auto_job.config import GreenhouseBoardConfig
from auto_job.ats import AtsDetectionResult
from auto_job.source_validation import (
    SourceValidationResult,
    validate_discovery_result,
    validate_greenhouse_board,
)


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


def test_validate_discovery_result_routes_to_provider_validator(monkeypatch):
    monkeypatch.setattr(
        "auto_job.source_validation.validate_greenhouse_board",
        lambda board_config: SourceValidationResult(
            provider="greenhouse",
            company=board_config.company,
            identifier=board_config.board_token,
            status="ok",
            job_count=3,
        ),
    )

    result = validate_discovery_result(
        AtsDetectionResult(
            provider="greenhouse",
            matched_pattern="boards.greenhouse.io",
            final_url="https://boards.greenhouse.io/example",
            ats_url="https://boards.greenhouse.io/example",
            company_slug="example",
        )
    )

    assert result.status == "ok"
    assert result.identifier == "example"
    assert result.job_count == 3


def test_validate_discovery_result_requires_company_slug():
    result = validate_discovery_result(
        AtsDetectionResult(
            provider="greenhouse",
            matched_pattern="boards.greenhouse.io",
            final_url="https://example.com",
        )
    )

    assert result.status == "error"
    assert result.message == "missing company slug"
