from html import unescape
import re


def clean_description(description: str) -> str:
    # Provider descriptions often arrive as HTML or escaped HTML. Normalize
    # tags/entities when the app needs plain text for scoring or text reports.
    for _ in range(2):
        description = unescape(description)

    description = re.sub(r"<[^>]+>", " ", description)
    description = description.replace("\xa0", " ")
    description = description.replace("&", " and ")
    description = re.sub(r"\b(?:nbsp|amp)\b", " ", description, flags=re.IGNORECASE)
    description = " ".join(description.split())

    return description
