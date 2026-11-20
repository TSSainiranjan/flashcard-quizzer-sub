"""Data ingestion and validation for flashcard JSON files.

Supports two JSON shapes:

* **Array format** -- a bare list of card objects::

      [{"front": "CPU", "back": "Central Processing Unit"}, ...]

* **Object format** -- a wrapper object with a ``"cards"`` key::

      {"cards": [{"front": "CPU", "back": "Central Processing Unit"}, ...]}

Any structural problem (missing file, invalid JSON syntax, missing
required fields, wrong types) is reported as a :class:`FlashcardDataError`
with a message suitable for showing directly to an end user -- callers
should never need to catch a raw ``json.JSONDecodeError`` or
``OSError``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

from flashcard import Flashcard, FlashcardDataError

REQUIRED_FIELDS = ("front", "back")


def load_flashcards(file_path: str) -> List[Flashcard]:
    """Load and validate flashcards from a JSON file.

    Args:
        file_path: Path to a JSON file in either array or object format.

    Returns:
        A list of validated :class:`Flashcard` instances, in file order.

    Raises:
        FlashcardDataError: If the file is missing, unreadable, not valid
            JSON, structurally wrong, or contains cards that are missing
            the required ``front``/``back`` fields.
    """
    path = Path(file_path)

    raw_text = _read_file(path)
    payload = _parse_json(raw_text, path)
    raw_cards = _extract_card_list(payload, path)

    if not raw_cards:
        raise FlashcardDataError(
            f"No flashcards found in '{path}'. Add at least one card with "
            '"front" and "back" fields.'
        )

    return [
        _to_flashcard(entry, index, path)
        for index, entry in enumerate(raw_cards)
    ]


def _read_file(path: Path) -> str:
    """Read the raw text of ``path``, raising a friendly error on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise FlashcardDataError(
            f"Could not find the flashcard file '{path}'. Check the path "
            "and try again."
        ) from exc
    except IsADirectoryError as exc:
        raise FlashcardDataError(
            f"'{path}' is a directory, not a flashcard JSON file."
        ) from exc
    except OSError as exc:
        raise FlashcardDataError(f"Could not read '{path}': {exc}") from exc


def _parse_json(raw_text: str, path: Path) -> Any:
    """Parse ``raw_text`` as JSON, raising a friendly error on failure."""
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise FlashcardDataError(
            f"'{path}' is not valid JSON (line {exc.lineno}, column "
            f"{exc.colno}): {exc.msg}. Please fix the file's syntax."
        ) from exc


def _extract_card_list(payload: Any, path: Path) -> List[Any]:
    """Pull the list of raw card entries out of either supported shape."""
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        if "cards" not in payload:
            raise FlashcardDataError(
                f"'{path}' is a JSON object but is missing a \"cards\" key. "
                'Expected either a list of cards or {"cards": [...]}.'
            )
        cards = payload["cards"]
        if not isinstance(cards, list):
            raise FlashcardDataError(
                f"'{path}': the \"cards\" field must be a list, got "
                f"{type(cards).__name__}."
            )
        return cards

    raise FlashcardDataError(
        f"'{path}' must contain a JSON array of cards or an object with a "
        f'"cards" array, got {type(payload).__name__}.'
    )


def _to_flashcard(entry: Any, index: int, path: Path) -> Flashcard:
    """Validate and convert a single raw JSON entry into a Flashcard."""
    if not isinstance(entry, dict):
        raise FlashcardDataError(
            f"'{path}': card #{index + 1} must be a JSON object, got "
            f"{type(entry).__name__}."
        )

    missing = [field for field in REQUIRED_FIELDS if field not in entry]
    if missing:
        raise FlashcardDataError(
            f"'{path}': card #{index + 1} is missing required field(s): "
            f"{', '.join(missing)}."
        )

    front, back = entry["front"], entry["back"]
    if not isinstance(front, str) or not front.strip():
        raise FlashcardDataError(
            f"'{path}': card #{index + 1} has an invalid \"front\" value; "
            "it must be a non-empty string."
        )
    if not isinstance(back, str) or not back.strip():
        raise FlashcardDataError(
            f"'{path}': card #{index + 1} has an invalid \"back\" value; "
            "it must be a non-empty string."
        )

    return Flashcard(front=front.strip(), back=back.strip())
