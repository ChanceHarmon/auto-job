import yaml


# Discovery writes back into the same user-owned config.yaml file. These helper
# builders keep generated entries consistent with hand-written config entries.
def build_greenhouse_board_config(
    company: str,
    board_token: str,
    discovered_via: str | None = None,
) -> dict:
    """Build a normalized Greenhouse config entry."""

    config = {
        "company": company,
        "board_token": board_token,
    }

    if discovered_via:
        config["discovered_via"] = discovered_via

    return config


def build_ashby_company_config(
    company: str,
    company_slug: str,
    discovered_via: str | None = None,
) -> dict:
    """Build a normalized Ashby config entry."""

    config = {
        "company": company,
        "company_slug": company_slug,
    }

    if discovered_via:
        config["discovered_via"] = discovered_via

    return config


def build_lever_company_config(
    company: str,
    company_slug: str,
    discovered_via: str | None = None,
) -> dict:
    """Build a normalized Lever config entry."""

    config = {
        "company": company,
        "company_slug": company_slug,
    }

    if discovered_via:
        config["discovered_via"] = discovered_via

    return config


def add_greenhouse_board(
    config_path: str,
    company: str,
    board_token: str,
) -> bool:
    """Add a Greenhouse board if it does not already exist."""

    with open(config_path, "r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file)

    # Use the provider identifier as the dedupe key because company display
    # names can vary while board tokens/slugs are stable.
    boards = config_data["sources"].setdefault(
        "greenhouse_boards",
        []
    )

    already_exists = any(
        board["board_token"] == board_token
        for board in boards
    )

    if already_exists:
        return False

    boards.append(
        build_greenhouse_board_config(
            company,
            board_token,
            discovered_via="rss",
        )
    )

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            config_data,
            file,
            sort_keys=False,
        )

    return True


def add_ashby_company(
    config_path: str,
    company: str,
    company_slug: str,
) -> bool:
    """Add an Ashby company if it does not already exist."""

    with open(config_path, "r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file)

    # Ashby and Lever use company_slug rather than board_token, but the write
    # flow mirrors Greenhouse: read config, skip duplicates, append, write back.
    companies = config_data["sources"].setdefault(
        "ashby_companies",
        []
    )

    already_exists = any(
        existing["company_slug"] == company_slug
        for existing in companies
    )

    if already_exists:
        return False

    companies.append(
        build_ashby_company_config(
            company,
            company_slug,
            discovered_via="rss",
        )
    )

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            config_data,
            file,
            sort_keys=False,
        )

    return True


def add_lever_company(
    config_path: str,
    company: str,
    company_slug: str,
) -> bool:
    """Add a Lever company if it does not already exist."""

    with open(config_path, "r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file)

    companies = config_data["sources"].setdefault(
        "lever_companies",
        []
    )

    already_exists = any(
        existing["company_slug"] == company_slug
        for existing in companies
    )

    if already_exists:
        return False

    companies.append(
        build_lever_company_config(
            company,
            company_slug,
            discovered_via="rss",
        )
    )

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(
            config_data,
            file,
            sort_keys=False,
        )

    return True


def add_provider_source(
    config_path: str,
    provider: str,
    company_slug: str,
) -> bool:
    """Add a detected ATS source to config.yaml."""

    if provider == "greenhouse":
        return add_greenhouse_board(config_path, company_slug.title(), company_slug)

    if provider == "ashby":
        return add_ashby_company(config_path, company_slug.title(), company_slug)

    if provider == "lever":
        return add_lever_company(config_path, company_slug.title(), company_slug)

    return False
