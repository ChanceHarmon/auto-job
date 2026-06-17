from typer.testing import CliRunner

from auto_job import cli
from auto_job.ats import AtsDetectionResult
from auto_job.models import Job
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
    assert "Validation summary:" in result.output


def test_validate_sources_command_can_show_only_problems(monkeypatch):
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
                company="Healthy Co",
                identifier="healthy",
                status="ok",
                job_count=12,
            ),
            SourceValidationResult(
                provider="lever",
                company="Broken Co",
                identifier="broken",
                status="error",
                message="HTTP 404",
            ),
        ],
    )

    result = runner.invoke(cli.app, ["validate-sources", "--problems-only"])

    assert result.exit_code == 0
    assert "greenhouse:healthy" not in result.output
    assert "lever:broken" in result.output
    assert "error: 1" in result.output


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


def test_guide_command_prints_recommended_workflow():
    result = runner.invoke(cli.app, ["guide"])

    assert result.exit_code == 0
    assert "Recommended workflow" in result.output
    assert "validate-sources --problems-only" in result.output
    assert "discover-from-rss --write" in result.output


def test_discover_from_rss_skips_invalid_sources_when_writing(monkeypatch):
    add_calls = []

    monkeypatch.setattr(
        cli,
        "load_config",
        lambda path="config.yaml": object(),
    )

    class FakeRSSSource:
        def __init__(self, app_config):
            pass

        def fetch_jobs(self):
            return [
                Job(
                    company="Example Co",
                    title="Backend Engineer",
                    source="rss",
                    posting_url="https://example.com/job",
                )
            ]

    monkeypatch.setattr(cli, "RSSSource", FakeRSSSource)
    monkeypatch.setattr(
        cli,
        "discover_ats_from_job_urls",
        lambda urls: [build_detection_result()],
    )
    monkeypatch.setattr(
        cli,
        "validate_discovery_result",
        lambda result: SourceValidationResult(
            provider="greenhouse",
            company="Example Co",
            identifier="example",
            status="error",
            message="HTTP 404",
        ),
    )
    monkeypatch.setattr(
        cli,
        "add_provider_source",
        lambda *args: add_calls.append(args),
    )

    result = runner.invoke(cli.app, ["discover-from-rss", "--write"])

    assert result.exit_code == 0
    assert "Skipped invalid source" in result.output
    assert add_calls == []
