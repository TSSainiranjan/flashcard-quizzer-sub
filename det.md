# Project Brief: Flashcard Quizzer CLI (Internal Onboarding Tool)

## Overview
A lightweight internal CLI tool -- a "Flashcard Quizzer" -- to help new hires memorize server acronyms, systems concepts, and glossary terms. The application runs entirely in a terminal, loads question/answer pairs from JSON files, supports multiple quiz sequencing modes, and provides clean architecture for future extensions (such as spaced-repetition algorithms).

## Functional Requirements
1. **Data Ingestion & Validation**:
   - Load flashcards from JSON files supporting two formats:
     - Bare array: `[{"front": "...", "back": "..."}, ...]`
     - Object wrapper: `{"cards": [{"front": "...", "back": "..."}]}`
   - Validate structure (presence of non-empty `front` and `back` strings, valid JSON, non-empty deck).
   - Graceful, user-friendly error handling with informative messages -- never expose raw Python tracebacks to the user.

2. **Interactive Quiz Loop**:
   - Present the `front` of each card, accept user answer via terminal input.
   - Perform case-insensitive, whitespace-trimmed comparison against the `back`.
   - Provide immediate feedback (colored green for correct, red for incorrect).
   - Clean interruption: user can type `exit`/`quit` or send EOF/Ctrl+C at any prompt to terminate gracefully.

3. **Quiz Modes**:
   - **Sequential**: Present cards in original file order (1 to N).
   - **Random**: Present cards in a single randomized shuffle.
   - **Adaptive**: Reprioritize and repeat cards the user answers incorrectly so they reappear sooner. Must include a guaranteed termination condition (attempt cap) to prevent infinite loops on stubborn errors.

4. **Session Reporting & Analytics**:
   - End-of-session summary table reporting: total questions asked, correct answers count, accuracy percentage, and list of missed terms (even on early exit).
   - `--stats` CLI flag providing an expanded breakdown of missed terms.

## Technical Requirements
- **Architecture**: Modular separation of concerns (data layer, quiz engine, presentation layer, CLI entry point).
- **Design Patterns**:
  - **Strategy Pattern**: Abstract `QuizMode` algorithm interface with interchangeable mode strategies, orchestrated by `QuizSession`.
  - **Factory Pattern**: `QuizModeFactory` mapping CLI flags to strategy instances without `if/elif` chains.
- **Type Safety**: Python type hints on all functions and methods.
- **Testing**: Comprehensive pytest suite achieving >80% test coverage (targeting >90%), covering happy paths, edge cases, and error conditions.
- **Code Quality**: Clean adherence to PEP 8, verified by `black`, `isort`, `flake8` (0 errors), and `mypy`.
