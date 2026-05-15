import yaml


def add_greenhouse_board(
    config_path: str,
    company: str,
    board_token: str,
) -> bool:
    """Add a Greenhouse board if it does not already exist."""

    with open(config_path, "r", encoding="utf-8") as file:
        config_data = yaml.safe_load(file)

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

    boards.append({
        "company": company,
        "board_token": board_token,
    })

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

    companies.append({
        "company": company,
        "company_slug": company_slug,
    })

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

    return False