"""Integration tests that drive the full quiz loop end-to-end (loader ->
quiz engine -> UI) the way main.run_quiz() does, without touching real
stdin/stdout beyond what pytest's capsys captures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator, List

import pytest

from flashcard import Flashcard
from main import run_quiz


def _canned_input(answers: List[str]):
    """Return a callable that yields ``answers`` in order, like input()."""
    iterator: Iterator[str] = iter(answers)

    def _input(_prompt: str) -> str:
        return next(iterator)

    return _input


@pytest.fixture
def three_cards() -> List[Flashcard]:
    return [
        Flashcard(front="CPU", back="Central Processing Unit"),
        Flashcard(front="RAM", back="Random Access Memory"),
        Flashcard(front="SSD", back="Solid State Drive"),
    ]


class TestFullSession:
    def test_full_session(self, three_cards: List[Flashcard], capsys) -> None:
        """Simulate user answering 3 questions and checking final stats."""
        answers = [
            "Central Processing Unit",  # correct
            "wrong answer",  # incorrect
            "Solid State Drive",  # correct
        ]

        result = run_quiz(
            three_cards,
            mode_name="sequential",
            input_func=_canned_input(answers),
        )

        assert result.total == 3
        assert result.correct == 2
        assert result.missed_terms == ["RAM"]
        assert result.accuracy == pytest.approx(66.6666, rel=1e-3)

        output = capsys.readouterr().out
        assert "Quiz Summary" in output
        assert "RAM" in output

    # Backward-compatible alias
    test_full_session_scores_three_questions = test_full_session

    def test_full_session_with_stats_flag_shows_detailed_breakdown(
        self, three_cards: List[Flashcard], capsys
    ) -> None:
        answers = ["Central Processing Unit", "nope", "Solid State Drive"]

        run_quiz(
            three_cards,
            mode_name="sequential",
            input_func=_canned_input(answers),
            show_detailed_stats=True,
        )

        output = capsys.readouterr().out
        assert "missed 1 unique term" in output

    def test_full_session_exit_command_ends_early(
        self, three_cards: List[Flashcard]
    ) -> None:
        answers = ["Central Processing Unit", "exit"]

        result = run_quiz(
            three_cards,
            mode_name="sequential",
            input_func=_canned_input(answers),
        )

        assert result.total == 1
        assert result.correct == 1

    def test_full_session_handles_keyboard_interrupt_gracefully(
        self, three_cards: List[Flashcard]
    ) -> None:
        def _interrupting_input(_prompt: str) -> str:
            raise KeyboardInterrupt

        result = run_quiz(
            three_cards,
            mode_name="sequential",
            input_func=_interrupting_input,
        )

        assert result.total == 0

    def test_full_session_handles_eof_gracefully(
        self, three_cards: List[Flashcard]
    ) -> None:
        def _eof_input(_prompt: str) -> str:
            raise EOFError

        result = run_quiz(
            three_cards, mode_name="sequential", input_func=_eof_input
        )

        assert result.total == 0

    def test_full_session_with_real_data_file(self, tmp_path: Path) -> None:
        """End-to-end: load a real JSON file, then run the quiz over it."""
        from utils.file_handler import load_flashcards

        data_file = tmp_path / "deck.json"
        data_file.write_text(
            '[{"front": "DNS", "back": "Domain Name System"}]',
            encoding="utf-8",
        )

        cards = load_flashcards(str(data_file))
        result = run_quiz(
            cards,
            mode_name="random",
            input_func=_canned_input(["Domain Name System"]),
        )

        assert result.total == 1
        assert result.correct == 1
