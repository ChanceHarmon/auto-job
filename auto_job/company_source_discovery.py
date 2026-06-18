from dataclasses import dataclass, field
from pathlib import Path
from time import sleep

import yaml

from auto_job.config import (
    AppConfig,
    AshbyCompanyConfig,
    GreenhouseBoardConfig,
    LeverCompanyConfig,
)
from auto_job.config_writer import (
    add_ashby_company,
    add_greenhouse_board,
    add_lever_company,
    remove_provider_source,
)
from auto_job.source_validation import (
    SourceValidationResult,
    validate_ashby_company,
    validate_greenhouse_board,
    validate_lever_company,
    validate_sources,
)


DEFAULT_COMPANY_UNIVERSE_PATH = Path("data/company_universe.yaml")
SUPPORTED_DISCOVERY_PROVIDERS = {"greenhouse", "lever", "ashby"}


@dataclass
class CompanyCandidate:
    name: str
    slugs: list[str]
    industries: list[str] = field(default_factory=list)


@dataclass
class CompanyDiscoveryResult:
    provider: str
    company: str
    slug: str
    status: str
    job_count: int = 0
    message: str = ""
    already_configured: bool = False
    added: bool = False


@dataclass
class DiscoveryMaintenanceResult:
    tested_count: int
    discoveries: list[CompanyDiscoveryResult]
    stale_sources: list[SourceValidationResult]
    added_count: int = 0
    pruned_count: int = 0


def slugify_company_name(name: str) -> str:
    slug = "".join(character.lower() for character in name if character.isalnum())
    return slug


def load_company_candidates(path: str | Path) -> list[CompanyCandidate]:
    with Path(path).open("r", encoding="utf-8") as file:
        raw_data = yaml.safe_load(file) or {}

    candidates = []

    for raw_company in raw_data.get("companies", []):
        name = raw_company["name"]
        slugs = raw_company.get("slugs") or [slugify_company_name(name)]

        candidates.append(
            CompanyCandidate(
                name=name,
                slugs=slugs,
                industries=raw_company.get("industries", []),
            )
        )

    return candidates


def get_configured_source_keys(app_config: AppConfig) -> set[tuple[str, str]]:
    configured_sources = set()

    for board in app_config.sources.greenhouse_boards:
        configured_sources.add(("greenhouse", board.board_token))

    for company in app_config.sources.lever_companies:
        configured_sources.add(("lever", company.company_slug))

    for company in app_config.sources.ashby_companies:
        configured_sources.add(("ashby", company.company_slug))

    return configured_sources


def validate_candidate_provider(
    provider: str,
    company_name: str,
    slug: str,
) -> SourceValidationResult:
    if provider == "greenhouse":
        return validate_greenhouse_board(
            GreenhouseBoardConfig(
                company=company_name,
                board_token=slug,
            )
        )

    if provider == "lever":
        return validate_lever_company(
            LeverCompanyConfig(
                company=company_name,
                company_slug=slug,
            )
        )

    if provider == "ashby":
        return validate_ashby_company(
            AshbyCompanyConfig(
                company=company_name,
                company_slug=slug,
            )
        )

    return SourceValidationResult(
        provider=provider,
        company=company_name,
        identifier=slug,
        status="error",
        message="unsupported provider",
    )


def is_discoverable_result(result: SourceValidationResult) -> bool:
    # For discovery, only boards with current jobs are added automatically.
    # Empty can be a real board, but adding every empty board makes daily runs
    # noisier without improving matches.
    return result.status == "ok" and result.job_count > 0


def is_prunable_source(result: SourceValidationResult) -> bool:
    # Only prune hard 404s. Empty boards, timeouts, and parse failures can be
    # temporary or simply mean "no jobs today".
    return result.status == "error" and result.message == "HTTP 404"


def add_discovered_source(
    config_path: str,
    provider: str,
    company: str,
    slug: str,
) -> bool:
    # The generic add_provider_source helper is still useful for URL-based
    # discovery, but this command already knows the real company name from the
    # company universe file. Preserve that name so generated config stays tidy.
    if provider == "greenhouse":
        return add_greenhouse_board(
            config_path,
            company,
            slug,
            discovered_via="company_universe",
        )

    if provider == "lever":
        return add_lever_company(
            config_path,
            company,
            slug,
            discovered_via="company_universe",
        )

    if provider == "ashby":
        return add_ashby_company(
            config_path,
            company,
            slug,
            discovered_via="company_universe",
        )

    return False


def discover_company_sources(
    app_config: AppConfig,
    config_path: str,
    company_file: str | Path = DEFAULT_COMPANY_UNIVERSE_PATH,
    providers: list[str] | None = None,
    limit: int | None = None,
    write: bool = False,
    prune_stale: bool = False,
    delay_seconds: float = 0,
    progress_callback=None,
    result_callback=None,
    phase_callback=None,
) -> DiscoveryMaintenanceResult:
    candidates = load_company_candidates(company_file)

    if limit:
        candidates = candidates[:limit]

    providers = providers or ["greenhouse", "lever", "ashby"]
    providers = [
        provider
        for provider in providers
        if provider in SUPPORTED_DISCOVERY_PROVIDERS
    ]
    configured_sources = get_configured_source_keys(app_config)
    discoveries = []
    added_count = 0

    for candidate in candidates:
        for slug in candidate.slugs:
            for provider in providers:
                if progress_callback:
                    progress_callback(provider, candidate.name, slug)

                validation_result = validate_candidate_provider(
                    provider,
                    candidate.name,
                    slug,
                )

                if result_callback:
                    result_callback(validation_result)

                already_configured = (provider, slug) in configured_sources

                if is_discoverable_result(validation_result):
                    added = False

                    if write and not already_configured:
                        added = add_discovered_source(
                            config_path,
                            provider,
                            candidate.name,
                            slug,
                        )

                        if added:
                            added_count += 1
                            configured_sources.add((provider, slug))

                    discoveries.append(
                        CompanyDiscoveryResult(
                            provider=provider,
                            company=candidate.name,
                            slug=slug,
                            status=validation_result.status,
                            job_count=validation_result.job_count,
                            message=validation_result.message,
                            already_configured=already_configured,
                            added=added,
                        )
                    )

                if delay_seconds:
                    sleep(delay_seconds)

    stale_sources = []
    pruned_count = 0

    if prune_stale:
        if phase_callback:
            phase_callback("Validating configured sources for stale 404s...")

        stale_sources = [
            result
            for result in validate_sources(app_config, progress_callback=progress_callback)
            if result.provider in providers and is_prunable_source(result)
        ]

    if write and prune_stale:
        for stale_source in stale_sources:
            removed = remove_provider_source(
                config_path,
                stale_source.provider,
                stale_source.identifier,
            )

            if removed:
                pruned_count += 1

    return DiscoveryMaintenanceResult(
        tested_count=len(candidates),
        discoveries=discoveries,
        stale_sources=stale_sources,
        added_count=added_count,
        pruned_count=pruned_count,
    )
