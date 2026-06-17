from typer.testing import CliRunner

from auto_job import cli
from auto_job.ats import AtsDetectionResult
from auto_job.source_validation import SourceValidationResult


runner = CliRunner()


def build_detection_result() -> AtsDetectionResult:
    return AtsDetectionResult(
        provider="greenhouse",
        matched_pattern="boards.greenhouse.io",
        final_url="https://example.com/careers",
        ats_url="https://boards.greenhouse.io/example",
        company_slug="example",
    )


def test_detect_ats_does_not_write_by_default(monkeypatch):
    add_calls = []

    monkeypatch.setattr(
        cli,
        "detect_ats_provider",
        lambda url: build_detection_result(),
    )
    monkeypatch.setattr(
        cli,
        "add_provider_source",
        lambda *args: add_calls.append(args),
    )

    result = runner.invoke(cli.app, ["detect-ats", "https://example.com/careers"])

    assert result.exit_code == 0
    assert "Detected ATS: greenhouse" in result.output
    assert add_calls == []


def test_detect_ats_writes_when_requested(monkeypatch):
    add_calls = []

    monkeypatch.setattr(
        cli,
        "detect_ats_provider",
        lambda url: build_detection_result(),
    )
    monkeypatch.setattr(
        cli,
        "add_provider_source",
        lambda *args: add_calls.append(args) or True,
    )

    result = runner.invoke(
        cli.app,
        ["detect-ats", "https://example.com/careers", "--write"],
    )

    assert result.exit_code == 0
    assert "Added board to config.yaml" in result.output
    assert add_calls == [
        (
            "config.yaml",
            "greenhouse",
            "example",
        )
    ]


def test_validate_sources_command_prints_results(monkeypatch):
    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: object(),
    )
    monkeypatch.setattr(
        cli,
        "validate_sources",
        lambda app_config: [
            SourceValidationResult(
                provider="greenhouse",
                company="Example Co",
                identifier="example",
                status="ok",
                job_count=12,
            )
        ],
    )

    result = runner.invoke(cli.app, ["validate-sources"])

    assert result.exit_code == 0
    assert "greenhouse:example" in result.output
    assert "ok, 12 jobs" in result.output


def test_run_command_validates_then_runs_search_workflow(monkeypatch):
    calls = []

    monkeypatch.setattr(
        cli,
        "load_config",
        lambda: object(),
    )
    monkeypatch.setattr(
        cli,
        "validate_sources",
        lambda app_config: calls.append("validate") or [],
    )
    monkeypatch.setattr(
        cli,
        "run_search_workflow",
        lambda app_config: calls.append("search"),
    )

    result = runner.invoke(cli.app, ["run"])

    assert result.exit_code == 0
    assert calls == ["validate", "search"]
