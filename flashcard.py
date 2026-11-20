"""Core data model for the Flashcard Quizzer application.

This module defines the ``Flashcard`` value object shared by every other
module in the project (data loading, quiz engine, UI) along with the
exception type used to signal recoverable data problems.
"""

from __future__ import annotations

from dataclasses import dataclass


class FlashcardDataError(Exception):
    """Raised when flashcard data cannot be loaded or is malformed.

    Callers (typically ``main.py``) are expected to catch this exception
    and print a friendly, human-readable message instead of letting a raw
    traceback reach the terminal.
    """


@dataclass(frozen=True)
class Flashcard:
    """A single question/answer pair used by the quiz engine.

    Attributes:
        front: The prompt shown to the user (the question).
        back: The expected answer, compared case-insensitively.
    """

    front: str
    back: str

    def is_correct(self, user_answer: str) -> bool:
        """Compare ``user_answer`` to this card's answer.

        The comparison is case-insensitive and ignores leading/trailing
        whitespace so that answers like ``" cpu "`` and ``"CPU"`` both
        match ``"CPU"``.

        Args:
            user_answer: The raw text typed by the user.

        Returns:
            True if the normalized answers match, False otherwise.
        """
        return user_answer.strip().casefold() == self.back.strip().casefold()
