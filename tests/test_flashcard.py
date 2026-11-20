"""Unit tests for the Flashcard value object itself."""

from __future__ import annotations

from flashcard import Flashcard


class TestFlashcard:
    def test_is_correct_matches_exact_answer(self) -> None:
        card = Flashcard(front="CPU", back="Central Processing Unit")
        assert card.is_correct("Central Processing Unit") is True

    def test_is_correct_is_case_insensitive(self) -> None:
        card = Flashcard(front="CPU", back="Central Processing Unit")
        assert card.is_correct("central processing unit") is True
        assert card.is_correct("CENTRAL PROCESSING UNIT") is True

    def test_is_correct_trims_whitespace(self) -> None:
        card = Flashcard(front="CPU", back="Central Processing Unit")
        assert card.is_correct("  Central Processing Unit  ") is True

    def test_is_correct_rejects_wrong_answer(self) -> None:
        card = Flashcard(front="CPU", back="Central Processing Unit")
        assert card.is_correct("Graphics Processing Unit") is False

    def test_flashcards_are_equal_by_value(self) -> None:
        a = Flashcard(front="CPU", back="Central Processing Unit")
        b = Flashcard(front="CPU", back="Central Processing Unit")
        assert a == b
