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