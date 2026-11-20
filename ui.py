"""Terminal presentation layer: colored feedback, prompts, and the
end-of-session summary table.

Every function that produces user-facing text is split into a pure
``format_*`` (or ``build_*``) function that returns a string, plus a thin
``print_*`` wrapper. Keeping the string-building logic pure makes it
trivial to unit test without capturing stdout.
"""

from __future__ import annotations

from typing import List

from colorama import Fore, Style
from colorama import init as colorama_init

from flashcard import Flashcard
from quiz_engine import QuizResult

colorama_init(autoreset=True)

EXIT_COMMANDS = {"exit", "quit"}


def format_question(card: Flashcard, index: int, total: int) -> str:
    """Format the prompt shown for a single flashcard.

    Args:
        card: The flashcard to present.
        index: 1-based position of this card in the session.
        total: Total number of cards in the deck (for the "X of Y" label).
    """
    return f"[{index}/{total}] {card.front}"


def format_feedback(correct: bool, correct_answer: str) -> str:
    """Format immediate correct/incorrect feedback for a submitted answer."""
    if correct:
        return f"{Fore.GREEN}Correct!{Style.RESET_ALL}"
    return (
        f"{Fore.RED}Incorrect.{Style.RESET_ALL} "
        f"The answer was: {correct_answer}"
    )


def format_summary(result: QuizResult) -> str:
    """Format the end-of-session summary table.

    Includes total questions asked, accuracy percentage, and the list of
    terms (card fronts) the user missed at least once.
    """
    lines = [
        "",
        "=" * 40,
        "Quiz Summary",
        "=" * 40,
        f"Total Questions : {result.total}",
        f"Correct Answers : {result.correct}",
        f"Accuracy        : {result.accuracy:.1f}%",
    ]

    if result.missed_terms:
        lines.append("Missed Terms    :")
        lines.extend(f"  - {term}" for term in result.missed_terms)
    else:
        lines.append("Missed Terms    : none")

    lines.append("=" * 40)
    return "\n".join(lines)


def format_error(message: str) -> str:
    """Format a user-facing error message in red, with no traceback."""
    return f"{Fore.RED}Error:{Style.RESET_ALL} {message}"


def format_welcome(mode_name: str, card_count: int) -> str:
    """Format the banner shown when a quiz session starts."""
    return (
        f"Starting {mode_name} quiz with {card_count} card(s).\n"
        "Type your answer and press Enter. "
        "Type 'exit' or press Ctrl+C to quit."
    )


def format_goodbye() -> str:
    """Format the message shown when the user exits early."""
    return "Goodbye! Thanks for practicing."


def is_exit_command(user_input: str) -> bool:
    """Return True if ``user_input`` should end the quiz session early."""
    return user_input.strip().lower() in EXIT_COMMANDS


def print_question(card: Flashcard, index: int, total: int) -> None:
    """Print the prompt for a single flashcard. See :func:`format_question`."""
    print(format_question(card, index, total))


def print_feedback(correct: bool, correct_answer: str) -> None:
    """Print colored feedback. See :func:`format_feedback`."""
    print(format_feedback(correct, correct_answer))


def print_summary(result: QuizResult) -> None:
    """Print the end-of-session summary table. See :func:`format_summary`."""
    print(format_summary(result))


def print_error(message: str) -> None:
    """Print a user-facing error message. See :func:`format_error`."""
    print(format_error(message))


def print_welcome(mode_name: str, card_count: int) -> None:
    """Print the session-start banner. See :func:`format_welcome`."""
    print(format_welcome(mode_name, card_count))


def print_goodbye() -> None:
    """Print the early-exit farewell message. See :func:`format_goodbye`."""
    print(format_goodbye())


def print_detailed_stats(missed_terms: List[str]) -> None:
    """Print a verbose breakdown, used when ``--stats`` is passed."""
    if not missed_terms:
        print("No missed terms this session -- great job!")
        return
    print(f"You missed {len(missed_terms)} unique term(s):")
    for term in missed_terms:
        print(f"  * {term}")
