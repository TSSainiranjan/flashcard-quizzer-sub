"""Unit tests for quiz_engine.py: the Strategy classes, the Factory, and
QuizSession's scoring/stats logic.
"""

from __future__ import annotations

from typing import List

import pytest

from flashcard import Flashcard
from quiz_engine import (
    AdaptiveMode,
    QuizModeFactory,
    QuizSession,
    RandomMode,
    SequentialMode,
)


def _drain(mode) -> List[Flashcard]:
    """Pull every card out of a QuizMode in the order it yields them."""
    drawn = []
    while mode.has_next():
        drawn.append(mode.next_card())
    return drawn


@pytest.fixture
def cards() -> List[Flashcard]:
    return [
        Flashcard(front="CPU", back="Central Processing Unit"),
        Flashcard(front="RAM", back="Random Access Memory"),
        Flashcard(front="SSD", back="Solid State Drive"),
    ]


class TestSequentialMode:
    def test_sequential_mode_preserves_order(
        self, cards: List[Flashcard]
    ) -> None:
        mode = SequentialMode(cards)
        assert _drain(mode) == cards

    def test_sequential_mode_exhausts_after_all_cards(
        self, cards: List[Flashcard]
    ) -> None:
        mode = SequentialMode(cards)
        _drain(mode)
        assert mode.has_next() is False

    def test_sequential_mode_rejects_empty_deck(self) -> None:
        with pytest.raises(ValueError):
            SequentialMode([])


class TestRandomMode:
    def test_random_mode_yields_every_card_exactly_once(
        self, cards: List[Flashcard]
    ) -> None:
        mode = RandomMode(cards)
        drawn = _drain(mode)
        assert sorted(drawn, key=lambda c: c.front) == sorted(
            cards, key=lambda c: c.front
        )
        assert len(drawn) == len(cards)

    def test_random_mode_can_produce_a_different_order(
        self, cards: List[Flashcard]
    ) -> None:
        """Not a strict guarantee, but with 3! = 6 orderings and 200 tries,
        seeing at least one different order from the original is a very
        safe bet; this guards against RandomMode silently degrading into
        SequentialMode.
        """
        original_order = [card.front for card in cards]
        saw_different_order = False
        for _ in range(200):
            mode = RandomMode(cards)
            drawn_order = [card.front for card in _drain(mode)]
            if drawn_order != original_order:
                saw_different_order = True
                break
        assert saw_different_order


class TestAdaptiveMode:
    def test_adaptive_mode_behavior(self, cards: List[Flashcard]) -> None:
        """Does it actually repeat incorrect questions? A card answered wrong
        should reappear later in the session.
        """
        mode = AdaptiveMode(cards)
        session = QuizSession(mode)

        first_card = session.next_card()
        session.submit_answer(first_card, "definitely wrong")

        remaining = _drain(mode)
        assert first_card in remaining

    # Backward-compatible alias for existing test runners
    test_adaptive_mode_repeats_incorrect_cards = test_adaptive_mode_behavior

    def test_adaptive_mode_does_not_repeat_correct_cards(
        self, cards: List[Flashcard]
    ) -> None:
        mode = AdaptiveMode(cards)
        session = QuizSession(mode)

        first_card = session.next_card()
        session.submit_answer(first_card, first_card.back)

        remaining = _drain(mode)
        assert first_card not in remaining

    def test_adaptive_mode_drops_card_after_max_attempts(
        self, cards: List[Flashcard]
    ) -> None:
        """A card wrong MAX_ATTEMPTS times in a row should stop reappearing,
        so a persistently-wrong card can't loop forever.
        """
        single_card = [cards[0]]
        mode = AdaptiveMode(single_card)

        attempts = 0
        while mode.has_next() and attempts < 50:
            card = mode.next_card()
            mode.record_result(card, correct=False)
            attempts += 1

        assert attempts == AdaptiveMode.MAX_ATTEMPTS
        assert mode.has_next() is False


class TestQuizModeFactory:
    @pytest.mark.parametrize(
        "mode_name, expected_type",
        [
            ("sequential", SequentialMode),
            ("Sequential", SequentialMode),
            ("random", RandomMode),
            ("RANDOM", RandomMode),
            ("adaptive", AdaptiveMode),
        ],
    )
    def test_quiz_mode_factory(
        self, mode_name: str, expected_type: type, cards: List[Flashcard]
    ) -> None:
        """Does the factory return the correct class object?"""
        mode = QuizModeFactory.create(mode_name, cards)
        assert isinstance(mode, expected_type)

    # Backward-compatible alias
    test_quiz_mode_factory_returns_correct_class = test_quiz_mode_factory

    def test_quiz_mode_factory_rejects_unknown_mode(
        self, cards: List[Flashcard]
    ) -> None:
        with pytest.raises(ValueError, match="Unknown quiz mode"):
            QuizModeFactory.create("spaced-repetition", cards)

    def test_available_modes_lists_all_registered_modes(self) -> None:
        assert QuizModeFactory.available_modes() == [
            "adaptive",
            "random",
            "sequential",
        ]


class TestQuizSession:
    def test_submit_answer_is_case_insensitive(
        self, cards: List[Flashcard]
    ) -> None:
        session = QuizSession(SequentialMode(cards))
        card = session.next_card()
        assert session.submit_answer(card, card.back.upper()) is True

    def test_submit_answer_ignores_surrounding_whitespace(
        self, cards: List[Flashcard]
    ) -> None:
        session = QuizSession(SequentialMode(cards))
        card = session.next_card()
        assert session.submit_answer(card, f"  {card.back}  ") is True

    def test_submit_wrong_answer_returns_false(
        self, cards: List[Flashcard]
    ) -> None:
        session = QuizSession(SequentialMode(cards))
        card = session.next_card()
        assert session.submit_answer(card, "totally wrong") is False

    def test_result_tracks_totals_and_accuracy(
        self, cards: List[Flashcard]
    ) -> None:
        session = QuizSession(SequentialMode(cards))
        c1 = session.next_card()
        session.submit_answer(c1, c1.back)
        c2 = session.next_card()
        session.submit_answer(c2, "wrong")
        c3 = session.next_card()
        session.submit_answer(c3, c3.back)

        result = session.get_result()
        assert result.total == 3
        assert result.correct == 2
        assert result.accuracy == pytest.approx(66.6666, rel=1e-3)

    def test_result_missed_terms_are_unique_and_ordered(
        self, cards: List[Flashcard]
    ) -> None:
        mode = AdaptiveMode(cards)
        session = QuizSession(mode)

        first = session.next_card()
        session.submit_answer(first, "wrong")  # first gets requeued

        # Answer the requeued copy of `first` wrong again, plus the others.
        while session.has_next():
            card = session.next_card()
            session.submit_answer(
                card, "still wrong" if card.front == first.front else card.back
            )

        result = session.get_result()
        assert result.missed_terms.count(first.front) == 1

    def test_result_accuracy_is_zero_with_no_questions(
        self, cards: List[Flashcard]
    ) -> None:
        session = QuizSession(SequentialMode(cards))
        assert session.get_result().accuracy == 0.0
