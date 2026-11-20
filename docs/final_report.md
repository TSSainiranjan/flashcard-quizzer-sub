# AI-Assisted Development Project Report

**Student Name:** Student  
**Project Title:** Flashcard Quizzer CLI  
**Date:** 2026-11-20

## Executive Summary

The Flashcard Quizzer CLI is a terminal study tool for learning server acronyms. Built with Claude Code, development followed a Decompose -> Generate -> Review -> Refine -> Verify workflow to build production-ready software.

The app ingests JSON flashcards, validates inputs case-insensitively, and provides ANSI feedback. It implements Sequential, Random, and Adaptive modes via Strategy and Factory patterns, ending with a summary table and accuracy metrics.

AI accelerated scaffolding and tests, while reviews caught issues like infinite loops and late-binding mocks. The codebase achieves 96.84% test coverage and passes all linting gates.

## Project Overview

### Problem Statement

Technical onboarding requires learning server acronyms quickly. Static lists lack engagement, while external web tools cause context switching. The Flashcard Quizzer is an internal CLI that consumes local JSON decks and adapts to user performance.

### Solution Approach

The architecture separates concerns across five modules:
- **`utils/file_handler.py`**: Ingests JSON decks, mapping errors to `FlashcardDataError`.
- **`flashcard.py`**: Immutable `Flashcard` dataclass with normalized equality.
- **`quiz_engine.py`**: Strategy modes (`QuizMode` ABC), `QuizModeFactory`, and `QuizSession`.
- **`ui.py`**: Pure formatters (`format_*`) separated from print wrappers for testing.
- **`main.py`**: CLI flags and interactive loop via an injectable input interface.

Stack: Python 3.10+, `argparse`, `colorama`, `pytest`, `black`, `isort`, `flake8`, `pycodestyle`, `mypy`.

### Final Features

- [x] Dual-format JSON deck ingestion (bare arrays and wrapper objects)
- [x] Traceback-free error handling with friendly user messages
- [x] Three quiz modes: Sequential, Random, and Adaptive
- [x] Strategy-based execution with dynamic Factory instantiation
- [x] Case-insensitive, whitespace-trimmed answer evaluation
- [x] Immediate real-time ANSI terminal feedback (green/red)
- [x] End-of-session summary table with accuracy calculation
- [x] Optional `--stats` flag for an itemized missed-terms breakdown
- [x] Graceful exit handling via `exit`/`quit`, EOF, or `Ctrl+C`

## AI Collaboration Experience

### AI Tools Used

- [x] Claude (Claude Code)
- [ ] GitHub Copilot
- [ ] ChatGPT
- [ ] Other: ________

### Collaboration Workflow

1. **Structuring**: Decomposed requirements into phased prompts specifying files, types, and interfaces.
2. **Delegation**: Used AI for module scaffolding, strategy hierarchies, and test generation.
3. **Review**: Audited code against `code_review_checklist.md`, running automated tests and linters.
4. **Refinement**: Directed targeted AI refactoring to resolve logic flaws found during testing.

### Most Valuable AI Interactions

#### Example 1: Strategy and Factory Pattern Scaffolding
**Context:** Needed an extensible architecture for card sequencing algorithms.  
**AI Prompt:** "Define abstract `QuizMode` ABC with `has_next()`, `next_card()`, and `record_result()`. Implement `SequentialMode`, `RandomMode`, `AdaptiveMode`, `QuizModeFactory`, and `QuizSession`."  
**AI Response:** Claude generated the Strategy hierarchy and dictionary-backed Factory cleanly in one pass.  
**Your Changes:** Added validation in `QuizMode.__init__` to reject empty decks and enforce positive card counts.  
**Outcome:** Cleanly decoupled core logic that passed initial structural checks.

#### Example 2: Bounded Termination Guard for Adaptive Quiz Mode
**Context:** Generated `AdaptiveMode` reinserted missed cards unconditionally, risking an infinite loop.  
**AI Prompt:** "Review adaptive requeue logic: if a user consistently misses a card, does the session terminate?"  
**AI Response:** Acknowledged the issue and suggested capping re-queue operations.  
**Your Changes:** Added `MAX_ATTEMPTS = 3` cap and an `_attempts` tracking dictionary, dropping cards once reached while retaining them in missed terms.  
**Outcome:** Authored `test_adaptive_mode_drops_card_after_max_attempts` proving the loop terminates deterministically.

#### Example 3: Resolving Early-Bound Dependency Injection in Testing
**Context:** CLI tests monkeypatching `builtins.input` failed with stdin-capture errors.  
**AI Prompt:** "Tests monkeypatch `builtins.input`, but `main()` still reads real stdin. Why isn't the patch taking effect?"  
**AI Response:** Diagnosed that `run_quiz(..., input_func=input)` evaluated its default argument at import time, binding before test fixtures ran.  
**Your Changes:** Modified `main()` to pass `input_func=input` explicitly at the call site.  
**Outcome:** Both CLI tests passed and input interception worked reliably.

### Challenges with AI Collaboration

- **Unstated Invariants**: AI fulfills explicit instructions but often omits boundary guards like loop termination bounds.
- **Runtime Binding Semantics**: AI suggestions occasionally miss Python runtime nuances, such as default parameter evaluation timing.
- **Linter Over-Relaxation**: AI models tend to disable linters globally rather than scoping fine-grained overrides.

## Software Engineering Practices

### Code Quality Measures

- [x] Code formatting (Black, isort)
- [x] Linting (flake8, pycodestyle, mypy)
- [x] Type hints on all functions and methods
- [x] Documentation/comments (docstrings on all 54 functions and classes)
- [x] Error handling (unified `FlashcardDataError` with zero tracebacks)

### Testing Strategy

Testing followed a comprehensive unit and integration approach across six test modules in `tests/`:
- **Ingestion (`test_flashcard_loader.py`)**: Tests arrays, objects, malformed JSON, and missing keys.
- **Strategies (`test_quiz_modes.py`)**: Verifies ordering, shuffle distribution, attempt limits, and factory lookup.
- **UI & CLI (`test_ui.py`, `test_cli.py`)**: Tests ANSI formatting, stats calculations, arguments, and exits.
- **Integration (`test_integration.py`)**: Drives complete end-to-end sessions with canned inputs.  
The suite contains 80 test items achieving **96.84% code coverage**.

### Design Patterns Used

- **Strategy Pattern:** `QuizMode` defines the sequencing interface (`has_next`, `next_card`, `record_result`). `SequentialMode`, `RandomMode`, and `AdaptiveMode` implement interchangeable algorithms. `QuizSession` acts as Context, delegating sequencing while tracking scores independently.
- **Factory Pattern:** `QuizModeFactory` encapsulates instantiation through a string registry dictionary, converting `--mode` flags into concrete instances without branching.

### Code Structure and Organization

- `flashcard.py`: Domain value object and custom exceptions.
- `utils/file_handler.py`: Filesystem I/O and schema validation.
- `quiz_engine.py`: Quiz algorithms and scoring session state.
- `ui.py`: Terminal presentation, ANSI styling, and table formatting.
- `main.py`: CLI arguments and interactive loop orchestration.

## Technical Challenges and Solutions

### Challenge 1: Bounded Termination in Adaptive Quiz Loops
**Problem:** Wrong cards were re-queued for re-attempts, risking an infinite loop on repeated failures.  
**Solution:** Added `MAX_ATTEMPTS = 3` and an attempt counter, dropping cards once reached while keeping them in missed terms.  
**AI Involvement:** Claude helped identify the infinite loop and scaffolded the counter logic.  
**Lessons Learned:** Requeue and retry logic must always include explicit termination boundaries.

### Challenge 2: Scoping Strict Linting and Typing Rules
**Problem:** Global `disallow_untyped_defs = true` produced 17 errors in `tests/*` on untyped pytest fixtures.  
**Solution:** Configured scoped mypy overrides for `tests.*` and `setup.cfg` exclusions for pycodestyle.  
**AI Involvement:** Claude suggested configuring targeted overrides rather than weakening global rules.  
**Lessons Learned:** Maintain standards by scoping configuration overrides rather than relaxing project-wide checks.

## Code Quality Analysis

### Metrics

- Lines of code: 653 source lines + 671 test lines across 13 Python files
- Test coverage: 96.84% (80 passed tests, 0 failures)
- Number of functions/classes: 54 across source modules
- Linting score: 0 errors across `black`, `isort`, `flake8`, `pycodestyle`, and `mypy`

### Self-Assessment

- **Code Readability:** 5/5 - Functions are concise, single-purpose, and use descriptive naming.
- **Code Maintainability:** 5/5 - Strategy and Factory patterns allow adding new modes without modifying existing classes.
- **Test Quality:** 5/5 - Tests validate functional behavior, boundary conditions, and error recovery.
- **Documentation:** 5/5 - Every class and function has docstrings; architecture and CLI usage are thoroughly documented.

## Learning Outcomes

### Technical Skills Developed
- Implemented Strategy and Factory patterns with abstract base classes.
- Used frozen dataclasses for immutable domain value objects.
- Applied callable dependency injection (`input_func`) for testing.
- Configured Python quality tooling (`pytest`, `black`, `flake8`, `mypy`).

### AI Collaboration Skills
- Crafted constraint-anchored prompts with explicit type and error specifications.
- Applied structured code review checklists to audit generated code.
- Identified AI blind spots regarding runtime state and termination bounds.

### Software Engineering Insights
- Validated design pattern value when multiple algorithms share an interface.
- Confirmed that automated test suites are essential when refactoring AI code.
- Demonstrated that precise interface specs ensure reliable AI generation.

## Reflection

### What Worked Well
Decomposing into modular milestones enabled steady verification. Comprehensive tests caught critical runtime bugs that were invisible during inspection.

### What Could Be Improved
Stipulating termination conditions and testing fixtures in initial prompts would have avoided rework during earlier phases.

### Future Enhancements
Future work includes SM-2 spaced repetition, persistent session tracking, and CSV/JSON report exports.

## Conclusion

Productive AI collaboration requires active engineering oversight. While Claude Code accelerated initial implementation, engineering rigor—design patterns, testing, PEP 8, static typing, and systematic code reviews—ensured production standards. The Flashcard Quizzer CLI is modular, resilient, and thoroughly tested.

## Appendices

### Appendix A: AI Interaction Log
Detailed prompt transcripts, code revisions, and decision rationales are documented in `docs/ai_edit_log.md` across 6 comprehensive entries.

### Appendix B: Code Statistics
The codebase contains 653 source lines and 671 test lines across 13 Python files. The 80-test suite runs in 0.30s with 96.84% statement coverage.

### Appendix C: Additional Resources
- Onboarding specification: `det.md`
- Design patterns guide: `docs/design_patterns.md`
- Prompting best practices: `ai_guidance/prompting_best_practices.md`
- Code review checklist: `ai_guidance/code_review_checklist.md`
