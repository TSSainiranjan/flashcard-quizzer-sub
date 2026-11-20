"""Unit tests for utils.file_handler.load_flashcards (data ingestion)."""

from __future__ import annotations

from pathlib import Path

import pytest

from flashcard import Flashcard, FlashcardDataError
from utils.file_handler import load_flashcards


def _write(tmp_path: Path, name: str, content: str) -> str:
    file_path = tmp_path / name
    file_path.write_text(content, encoding="utf-8")
    return str(file_path)


class TestArrayFormat:
    def test_load_valid_flashcards_array(self, tmp_path: Path) -> None:
        """A bare JSON list of cards should load in file order."""
        path = _write(
            tmp_path,
            "array.json",
            '[{"front": "CPU", "back": "Central Processing Unit"}, '
            '{"front": "RAM", "back": "Random Access Memory"}]',
        )

        cards = load_flashcards(path)

        assert cards == [
            Flashcard(front="CPU", back="Central Processing Unit"),
            Flashcard(front="RAM", back="Random Access Memory"),
        ]


class TestObjectFormat:
    def test_load_valid_flashcards_object(self, tmp_path: Path) -> None:
        """A {"cards": [...]} wrapper object should load correctly."""
        path = _write(
            tmp_path,
            "object.json",
            '{"cards": [{"front": "DNS", "back": "Domain Name System"}]}',
        )

        cards = load_flashcards(path)

        assert cards == [Flashcard(front="DNS", back="Domain Name System")]

    def test_object_missing_cards_key_raises(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "no_cards.json", '{"deck": []}')

        with pytest.raises(FlashcardDataError, match="cards"):
            load_flashcards(path)

    def test_object_cards_not_a_list_raises(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "bad_cards.json", '{"cards": "nope"}')

        with pytest.raises(FlashcardDataError, match="must be a list"):
            load_flashcards(path)


class TestErrorHandling:
    def test_load_missing_file(self, tmp_path: Path) -> None:
        """Missing file should raise friendly error, not FileNotFoundError."""
        missing = str(tmp_path / "does_not_exist.json")

        with pytest.raises(FlashcardDataError, match="Could not find"):
            load_flashcards(missing)

    def test_load_invalid_json(self, tmp_path: Path) -> None:
        """Malformed JSON raises FlashcardDataError, not JSONDecodeError."""
        path = _write(tmp_path, "broken.json", "{not valid json")

        with pytest.raises(FlashcardDataError, match="not valid JSON"):
            load_flashcards(path)

    def test_load_missing_required_field(self, tmp_path: Path) -> None:
        """A card missing the 'back' field should be rejected."""
        path = _write(tmp_path, "missing_back.json", '[{"front": "CPU"}]')

        with pytest.raises(FlashcardDataError, match="back"):
            load_flashcards(path)

    def test_load_missing_front_field(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path,
            "missing_front.json",
            '[{"back": "Central Processing Unit"}]',
        )

        with pytest.raises(FlashcardDataError, match="front"):
            load_flashcards(path)

    def test_load_empty_array_raises(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "empty.json", "[]")

        with pytest.raises(FlashcardDataError, match="No flashcards found"):
            load_flashcards(path)

    def test_load_top_level_not_list_or_object(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "scalar.json", "42")

        with pytest.raises(
            FlashcardDataError, match="must contain a JSON array"
        ):
            load_flashcards(path)

    def test_card_entry_not_an_object(self, tmp_path: Path) -> None:
        path = _write(tmp_path, "bad_entry.json", '["just a string"]')

        with pytest.raises(FlashcardDataError, match="must be a JSON object"):
            load_flashcards(path)

    def test_front_must_be_non_empty_string(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path, "blank_front.json", '[{"front": "   ", "back": "x"}]'
        )

        with pytest.raises(FlashcardDataError, match="front"):
            load_flashcards(path)

    def test_back_must_be_non_empty_string(self, tmp_path: Path) -> None:
        path = _write(
            tmp_path, "blank_back.json", '[{"front": "x", "back": ""}]'
        )

        with pytest.raises(FlashcardDataError, match="back"):
            load_flashcards(path)

    def test_load_directory_instead_of_file(self, tmp_path: Path) -> None:
        with pytest.raises(FlashcardDataError, match="directory"):
            load_flashcards(str(tmp_path))

    def test_error_message_has_no_traceback_noise(
        self, tmp_path: Path
    ) -> None:
        """Exception message should read like a sentence, not a dump."""
        path = _write(tmp_path, "broken.json", "{bad")

        with pytest.raises(FlashcardDataError) as exc_info:
            load_flashcards(path)

        assert "Traceback" not in str(exc_info.value)
