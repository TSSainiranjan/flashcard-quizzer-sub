"""Unit tests for ui.py's pure string-formatting functions."""

from __future__ import annotations

import ui
from flashcard import Flashcard
from quiz_engine import QuizResult


class TestFormatting:
    def test_format_question_includes_front_and_position(self) -> None:
        card = Flashcard(front="CPU", back="Central Processing Unit")
        text = ui.format_question(card, index=2, total=5)
        assert "CPU" in text
        assert "2/5" in text

    def test_format_feedback_correct_mentions_correct(self) -> None:
        text = ui.format_feedback(True, "Central Processing Unit")
        assert "Correct" in text

    def test_format_feedback_incorrect_shows_answer(self) -> None:
        text = ui.format_feedback(False, "Central Processing Unit")
        assert "Incorrect" in text
        assert "Central Processing Unit" in text

    def test_format_summary_reports_totals_and_accuracy(self) -> None:
        result = QuizResult(total=4, correct=3, missed_terms=["CPU"])
        text = ui.format_summary(result)
        assert "Total Questions : 4" in text
        assert "Correct Answers : 3" in text
        assert "75.0%" in text
        assert "CPU" in text

    def test_format_summary_with_no_missed_terms(self) -> None:
        result = QuizResult(total=2, correct=2, missed_terms=[])
        text = ui.format_summary(result)
        assert "Missed Terms    : none" in text

    def test_format_error_prefixes_with_error(self) -> None:
        text = ui.format_error("file not found")
        assert "Error" in text
        assert "file not found" in text

    def test_format_welcome_includes_mode_and_count(self) -> None:
        text = ui.format_welcome("adaptive", 10)
        assert "adaptive" in text
        assert "10" in text

    def test_format_goodbye_is_nonempty(self) -> None:
        assert ui.format_goodbye()


class TestExitCommand:
    def test_exit_command_recognized_case_insensitively(self) -> None:
        assert ui.is_exit_command("exit") is True
        assert ui.is_exit_command("EXIT") is True
        assert ui.is_exit_command("  quit  ") is True

    def test_non_exit_command_not_recognized(self) -> None:
        assert ui.is_exit_command("Central Processing Unit") is False


class TestPrintWrappers:
    """Smoke-test the print_* wrappers to ensure they don't raise and
    delegate to the pure formatters (captured via capsys)."""

    def test_print_question(self, capsys) -> None:
        card = Flashcard(front="CPU", back="Central Processing Unit")
        ui.print_question(card, 1, 3)
        assert "CPU" in capsys.readouterr().out

    def test_print_feedback(self, capsys) -> None:
        ui.print_feedback(True, "answer")
        assert "Correct" in capsys.readouterr().out

    def test_print_summary(self, capsys) -> None:
        ui.print_summary(QuizResult(total=1, correct=1, missed_terms=[]))
        assert "Quiz Summary" in capsys.readouterr().out

    def test_print_error(self, capsys) -> None:
        ui.print_error("boom")
        assert "boom" in capsys.readouterr().out

    def test_print_welcome(self, capsys) -> None:
        ui.print_welcome("sequential", 5)
        assert "sequential" in capsys.readouterr().out

    def test_print_goodbye(self, capsys) -> None:
        ui.print_goodbye()
        assert capsys.readouterr().out.strip()

    def test_print_detailed_stats_with_missed_terms(self, capsys) -> None:
        ui.print_detailed_stats(["CPU", "RAM"])
        out = capsys.readouterr().out
        assert "CPU" in out and "RAM" in out

    def test_print_detailed_stats_with_no_missed_terms(self, capsys) -> None:
        ui.print_detailed_stats([])
        assert "great job" in capsys.readouterr().out.lower()
