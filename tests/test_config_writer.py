import yaml

from auto_job.config_writer import (
    add_ashby_company,
    add_greenhouse_board,
)


def test_add_greenhouse_board_adds_new_board(tmp_path):
    config_path = tmp_path / "config.yaml"

    config_data = {
        "sources": {}
    }

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(config_data, file)

    added = add_greenhouse_board(
        config_path,
        "ExampleCo",
        "exampleCo",
    )

    assert added is True

    with open(config_path, "r", encoding="utf-8") as file:
        updated_config = yaml.safe_load(file)

    boards = updated_config["sources"]["greenhouse_boards"]

    assert len(boards) == 1
    assert boards[0]["company"] == "ExampleCo"
    assert boards[0]["board_token"] == "exampleCo"


def test_add_greenhouse_board_prevents_duplicates(tmp_path):
    config_path = tmp_path / "config.yaml"

    config_data = {
        "sources": {
            "greenhouse_boards": [
                {
                    "company": "ExampleCo",
                    "board_token": "exampleco",
                }
            ]
        }
    }

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(config_data, file)

    added = add_greenhouse_board(config_path, "ExampleCo", "exampleco")

    assert added is False

    with open(config_path, "r", encoding="utf-8") as file:
        updated_config = yaml.safe_load(file)

    boards = updated_config["sources"]["greenhouse_boards"]

    assert len(boards) == 1


def test_add_ashby_company_adds_new_companies(tmp_path):
    config_path = tmp_path / "config.yaml"

    config_data = {
        "sources": {}
    }

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(config_data, file)

    added = add_ashby_company(
        config_path,
        "ExampleCo",
        "exampleCo",
    )

    assert added is True

    with open(config_path, "r", encoding="utf-8") as file:
        updated_config = yaml.safe_load(file)

    boards = updated_config["sources"]["ashby_companies"]

    assert len(boards) == 1
    assert boards[0]["company"] == "ExampleCo"
    assert boards[0]["company_slug"] == "exampleCo"


def test_add_ashby_companies_prevents_duplicates(tmp_path):
    config_path = tmp_path / "config.yaml"

    config_data = {
        "sources": {
            "ashby_companies": [
                {
                    "company": "ExampleCo",
                    "company_slug": "exampleco",
                }
            ]
        }
    }

    with open(config_path, "w", encoding="utf-8") as file:
        yaml.safe_dump(config_data, file)

    added = add_ashby_company(config_path, "ExampleCo", "exampleco")

    assert added is False

    with open(config_path, "r", encoding="utf-8") as file:
        updated_config = yaml.safe_load(file)

    boards = updated_config["sources"]["ashby_companies"]

    assert len(boards) == 1