"""Flashcard Quizzer CLI entry point.

Usage:
    python main.py --help
    python main.py --mode sequential --file data/glossary.json
    python main.py -m adaptive -f data/python_basics.json --stats
"""

from __future__ import annotations

import argparse
import sys
from typing import Callable, List, Optional, Sequence

import ui
from flashcard import Flashcard, FlashcardDataError
from quiz_engine import QuizModeFactory, QuizResult, QuizSession
from utils.file_handler import load_flashcards

DEFAULT_DATA_FILE = "data/glossary.json"


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="main.py",
        description=(
            "Flashcard Quizzer -- practice terms from a JSON deck "
            "right in your terminal."
        ),
    )
    parser.add_argument(
        "-f",
        "--file",
        default=DEFAULT_DATA_FILE,
        help='Path to a JSON flashcard file (array or {"cards": [...]} '
        "format). Default: %(default)s",
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=QuizModeFactory.available_modes(),
        default="sequential",
        help="Quiz mode: how cards are ordered. Default: %(default)s",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print a detailed breakdown of missed terms after the "
        "summary table.",
    )
    return parser


def run_quiz(
    cards: List[Flashcard],
    mode_name: str,
    input_func: Callable[[str], str] = input,
    show_detailed_stats: bool = False,
) -> QuizResult:
    """Run an interactive quiz loop over ``cards`` and return the result.

    Args:
        cards: The flashcards to quiz on (already loaded and validated).
        mode_name: The quiz mode name understood by ``QuizModeFactory``.
        input_func: Function used to read a line of user input; injectable
            for testing so tests never touch real stdin.
        show_detailed_stats: If True, print a verbose missed-terms
            breakdown in addition to the summary table.

    Returns:
        The final :class:`~quiz_engine.QuizResult` for the session.
    """
    mode = QuizModeFactory.create(mode_name, cards)
    session = QuizSession(mode)
    ui.print_welcome(mode_name, len(cards))

    index = 0
    while session.has_next():
        card = session.next_card()
        index += 1
        ui.print_question(card, index, len(cards))

        try:
            answer = input_func("> ")
        except (EOFError, KeyboardInterrupt):
            print()
            ui.print_goodbye()
            break

        if ui.is_exit_command(answer):
            ui.print_goodbye()
            break

        correct = session.submit_answer(card, answer)
        ui.print_feedback(correct, card.back)

    result = session.get_result()
    ui.print_summary(result)
    if show_detailed_stats:
        ui.print_detailed_stats(result.missed_terms)

    return result


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point. Returns a process exit code (0 = success)."""
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    try:
        cards = load_flashcards(args.file)
    except FlashcardDataError as exc:
        ui.print_error(str(exc))
        return 1

    try:
        # `input_func=input` is passed explicitly (rather than relying on
        # run_quiz's default parameter) so it's looked up at call time --
        # this is what lets tests monkeypatch `builtins.input` and have it
        # actually take effect.
        run_quiz(
            cards, args.mode, input_func=input, show_detailed_stats=args.stats
        )
    except ValueError as exc:
        ui.print_error(str(exc))
        return 1
    except KeyboardInterrupt:
        print()
        ui.print_goodbye()
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
