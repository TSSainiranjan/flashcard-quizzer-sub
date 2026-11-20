"""Quiz engine: card-ordering strategies, a factory to select them, and
the session object that runs the quiz loop and tracks statistics.

Design patterns
----------------
**Strategy** -- :class:`QuizMode` defines the interface for "how to pick
the next card." :class:`SequentialMode`, :class:`RandomMode`, and
:class:`AdaptiveMode` are interchangeable implementations of that
interface; :class:`QuizSession` (the context) doesn't know or care which
one it holds. Adding a new mode -- e.g. a future spaced-repetition mode
-- only requires a new ``QuizMode`` subclass; no existing code changes.

**Factory** -- :class:`QuizModeFactory` maps a user-supplied mode name
(from the ``--mode`` CLI flag) to the correct ``QuizMode`` subclass, so
callers never need an if/elif chain over mode names.
"""

from __future__ import annotations

import random
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Dict, List, Type

from flashcard import Flashcard


class QuizMode(ABC):
    """Abstract base class (Strategy interface) for card algorithms."""

    def __init__(self, cards: List[Flashcard]) -> None:
        """Store the deck this strategy will serve cards from.

        Args:
            cards: The flashcards to quiz on; must be non-empty.
        """
        if not cards:
            raise ValueError("QuizMode requires at least one flashcard.")
        self._cards = list(cards)

    @abstractmethod
    def has_next(self) -> bool:
        """Return True if another card is available."""

    @abstractmethod
    def next_card(self) -> Flashcard:
        """Return the next card to present, removing it from the queue."""

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Notify the strategy of the outcome of a card (default: no-op).

        Only :class:`AdaptiveMode` cares about this; sequential and random
        modes simply ignore it.
        """


class SequentialMode(QuizMode):
    """Presents cards in file order, 1 through N."""

    def __init__(self, cards: List[Flashcard]) -> None:
        """Queue up ``cards`` in their original file order."""
        super().__init__(cards)
        self._queue: Deque[Flashcard] = deque(self._cards)

    def has_next(self) -> bool:
        """Return True while cards remain in file order."""
        return bool(self._queue)

    def next_card(self) -> Flashcard:
        """Return the next card in file order."""
        return self._queue.popleft()


class RandomMode(QuizMode):
    """Presents cards in a shuffled order (the full deck, once each)."""

    def __init__(self, cards: List[Flashcard]) -> None:
        """Shuffle ``cards`` once and queue up the resulting order."""
        super().__init__(cards)
        shuffled = list(self._cards)
        random.shuffle(shuffled)
        self._queue: Deque[Flashcard] = deque(shuffled)

    def has_next(self) -> bool:
        """Return True while shuffled cards remain."""
        return bool(self._queue)

    def next_card(self) -> Flashcard:
        """Return the next card in shuffled order."""
        return self._queue.popleft()


class AdaptiveMode(QuizMode):
    """Prioritizes cards the user previously got wrong.

    Every card starts in the queue once. When a card is answered
    incorrectly it is reinserted a few positions ahead so it comes back
    around sooner, up to :data:`MAX_ATTEMPTS` times per card -- after
    that it is dropped so a stubbornly-wrong card can't loop forever.
    """

    MAX_ATTEMPTS = 3
    REQUEUE_OFFSET = 2

    def __init__(self, cards: List[Flashcard]) -> None:
        """Queue up ``cards`` and reset the per-card attempt counter."""
        super().__init__(cards)
        self._queue: Deque[Flashcard] = deque(self._cards)
        self._attempts: Dict[str, int] = {}

    def has_next(self) -> bool:
        """Return True while cards remain (including requeued ones)."""
        return bool(self._queue)

    def next_card(self) -> Flashcard:
        """Return the next card, which may be a previously-missed one."""
        return self._queue.popleft()

    def record_result(self, card: Flashcard, correct: bool) -> None:
        """Requeue ``card`` if wrong, up to :data:`MAX_ATTEMPTS` times."""
        if correct:
            return

        attempts = self._attempts.get(card.front, 0) + 1
        self._attempts[card.front] = attempts

        if attempts < self.MAX_ATTEMPTS:
            insert_at = min(self.REQUEUE_OFFSET, len(self._queue))
            self._queue.insert(insert_at, card)


class QuizModeFactory:
    """Factory that builds the correct :class:`QuizMode` for a mode name."""

    _registry: Dict[str, Type[QuizMode]] = {
        "sequential": SequentialMode,
        "random": RandomMode,
        "adaptive": AdaptiveMode,
    }

    @classmethod
    def create(cls, mode_name: str, cards: List[Flashcard]) -> QuizMode:
        """Instantiate the ``QuizMode`` registered for ``mode_name``.

        Args:
            mode_name: One of ``"sequential"``, ``"random"``, ``"adaptive"``
                (case-insensitive).
            cards: The flashcards to quiz on.

        Raises:
            ValueError: If ``mode_name`` isn't a registered mode.
        """
        mode_cls = cls._registry.get(mode_name.strip().lower())
        if mode_cls is None:
            available = ", ".join(sorted(cls._registry))
            raise ValueError(
                f"Unknown quiz mode '{mode_name}'. "
                f"Available modes: {available}."
            )
        return mode_cls(cards)

    @classmethod
    def available_modes(cls) -> List[str]:
        """Return the sorted list of registered mode names."""
        return sorted(cls._registry)


@dataclass
class QuizResult:
    """Immutable summary of a finished (or in-progress) quiz session."""

    total: int
    correct: int
    missed_terms: List[str] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        """Accuracy as a percentage from 0.0 to 100.0 (0.0 if no questions)."""
        if self.total == 0:
            return 0.0
        return (self.correct / self.total) * 100.0


class QuizSession:
    """Runs the answer-checking / stats-tracking side of a quiz.

    ``QuizSession`` is the Strategy pattern's *context*: it holds a
    ``QuizMode`` and delegates card ordering to it entirely.
    """

    def __init__(self, mode: QuizMode) -> None:
        """Start a new session scored against zero questions asked.

        Args:
            mode: The card-ordering strategy this session delegates to.
        """
        self._mode = mode
        self._total = 0
        self._correct = 0
        self._missed_terms: List[str] = []
        self._seen_missed: set = set()

    def has_next(self) -> bool:
        """Return True if there are more cards to present."""
        return self._mode.has_next()

    def next_card(self) -> Flashcard:
        """Return the next card to present, per the active strategy."""
        return self._mode.next_card()

    def submit_answer(self, card: Flashcard, user_answer: str) -> bool:
        """Score ``user_answer`` against ``card`` and update statistics.

        Args:
            card: The flashcard being answered.
            user_answer: The raw text the user typed.

        Returns:
            True if the answer was correct, False otherwise.
        """
        correct = card.is_correct(user_answer)
        self._total += 1
        if correct:
            self._correct += 1
        elif card.front not in self._seen_missed:
            self._seen_missed.add(card.front)
            self._missed_terms.append(card.front)

        self._mode.record_result(card, correct)
        return correct

    def get_result(self) -> QuizResult:
        """Return a snapshot of the session's statistics so far."""
        return QuizResult(
            total=self._total,
            correct=self._correct,
            missed_terms=list(self._missed_terms),
        )
