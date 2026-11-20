# Flashcard Quizzer

A terminal flashcard quiz app built for new-hire onboarding (memorizing
server acronyms, glossary terms, etc.), built with AI-assisted
development as a course project. Loads cards from JSON, quizzes you in
Sequential, Random, or Adaptive mode, and reports session stats at the
end.

## Features

- **Dual JSON input formats** -- a bare array of cards, or a
  `{"cards": [...]}` wrapper object.
- **Graceful error handling** -- a missing file, malformed JSON, or a
  card missing `front`/`back` prints a one-line, human-readable message
  and exits cleanly; never a Python traceback.
- **Three quiz modes** (Strategy pattern) -- `sequential`, `random`, and
  `adaptive` (repeats cards you got wrong, up to 3 attempts each, so a
  persistently-missed card can't loop the session forever).
- **Mode selection via Factory pattern** -- `QuizModeFactory` maps the
  `--mode` CLI flag to the right strategy class.
- **Colored terminal feedback** -- green for correct, red for incorrect
  (via `colorama`, cross-platform including Windows terminals).
- **Session summary table** -- total questions, accuracy %, and the list
  of missed terms, shown even if you exit early.
- **`--stats` flag** -- an extra verbose breakdown of exactly which terms
  you missed.
- **Graceful exit** -- type `exit`/`quit`, or press Ctrl+C, at any point.

## Installation

Requires Python 3.10+.

```bash
# 1. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# See all available flags
python main.py --help

# Sequential quiz over the sample server-acronym glossary
python main.py --mode sequential --file data/glossary.json

# Adaptive quiz over the Python basics deck, with a detailed missed-terms breakdown
python main.py -m adaptive -f data/python_basics.json --stats

# Random order, default file (data/glossary.json)
python main.py -m random
```

At any prompt, type your answer and press Enter, or type `exit` (or press
Ctrl+C) to end the session early -- the summary table is still shown.

### Example session

```
$ python main.py -m sequential -f data/glossary.json
Starting sequential quiz with 12 card(s).
Type your answer and press Enter. Type 'exit' or press Ctrl+C to quit.
[1/12] CPU
> Central Processing Unit
Correct!
[2/12] RAM
> ran memory
Incorrect. The answer was: Random Access Memory
...
========================================
Quiz Summary
========================================
Total Questions : 12
Correct Answers : 11
Accuracy        : 91.7%
Missed Terms    :
  - RAM
========================================
```

### Bring your own deck

Either JSON shape works:

```json
[
  {"front": "CPU", "back": "Central Processing Unit"},
  {"front": "RAM", "back": "Random Access Memory"}
]
```

```json
{
  "cards": [
    {"front": "CPU", "back": "Central Processing Unit"}
  ]
}
```

## Project Structure

```
flashcard-quizzer/
├── main.py                    # CLI entry point (argparse, quiz loop orchestration)
├── flashcard.py                # Flashcard data model + FlashcardDataError
├── quiz_engine.py              # QuizMode (Strategy) + QuizModeFactory + QuizSession
├── ui.py                       # Terminal presentation (color, prompts, summary table)
├── det.md                      # Problem specification & requirements ticket
├── ai_edit_log.md              # AI interaction review log (root copy)
├── prompts.md                  # Prompt log used to build this project
├── utils/
│   └── file_handler.py         # JSON loading & validation (data layer)
├── data/
│   ├── glossary.json           # Sample deck: server acronyms (array format)
│   └── python_basics.json      # Sample deck: Python basics (object format)
├── tests/                      # pytest suite (73 tests, 96.8% coverage)
├── docs/
│   ├── final_report.md         # Final project report (1000-1500 words)
│   ├── report_template.md      # Course final report template
│   ├── ai_edit_log.md          # Detailed AI interaction / review log
│   ├── design_patterns.md      # Course design patterns guide
│   └── project_rubric.md       # Project rubric and grading criteria
├── ai_guidance/
│   ├── code_review_checklist.md # AI code review checklist
│   └── prompting_best_practices.md # Prompting techniques guide
├── .claude/
│   ├── CLAUDE.md               # Claude configuration & course guidelines
│   ├── mcp.json                # MCP dev tools & workflow configuration
│   └── commands/               # AI workflow command templates
├── requirements.txt
├── setup.cfg                   # flake8 + pytest/coverage config
└── pyproject.toml              # black, isort, mypy config
```

## Design Patterns

- **Strategy** (`quiz_engine.py`): `QuizMode` is an abstract base class
  defining `has_next()`, `next_card()`, and `record_result()`.
  `SequentialMode`, `RandomMode`, and `AdaptiveMode` are interchangeable
  implementations. `QuizSession` (the Strategy context) doesn't know or
  care which mode it holds, which is what makes adding a future mode
  (e.g. real spaced repetition) a matter of writing one new class, not
  editing the quiz loop.
- **Factory** (`QuizModeFactory` in `quiz_engine.py`): translates the
  `--mode` CLI string into the correct `QuizMode` subclass via a
  registry dict, so `main.py` never needs an if/elif chain over mode
  names.

## Testing

```bash
# Run the full suite
python -m pytest

# Coverage report (HTML)
python -m pytest --cov=. --cov-report=html
# open htmlcov/index.html
```

73 tests across `tests/test_flashcard.py`, `tests/test_flashcard_loader.py`,
`tests/test_quiz_modes.py`, `tests/test_ui.py`, `tests/test_cli.py`, and
`tests/test_integration.py`. Current coverage: **96.8%** (target: >80%,
enforced automatically via `--cov-fail-under=80` in `setup.cfg`).

## Code Quality

```bash
black .        # formatting
isort .        # import order
flake8 .       # linting
mypy .         # static type checking
```

All four pass clean on the current codebase (mypy's `disallow_untyped_defs`
is scoped to source files only; test files use a relaxed override for
pytest's own fixture parameters -- see `docs/ai_edit_log.md` Entry 4 for
why).

## AI-Assisted Development & Documentation

This project was built collaboratively with Claude (Claude Code) following
a decompose -> generate -> review -> refine -> verify workflow:

- [`docs/final_report.md`](docs/final_report.md) -- the comprehensive final project report reflecting on AI collaboration, engineering practices, and learnings.
- [`prompts.md`](prompts.md) -- the specific prompts used, phase by phase.
- [`docs/ai_edit_log.md`](docs/ai_edit_log.md) (and [`ai_edit_log.md`](ai_edit_log.md)) -- six detailed
  interactions documenting bugs found in AI-generated code (an unbounded
  retry loop in `AdaptiveMode`, a late-binding default-argument bug that
  broke test mocking, an over-broad mypy rule, data validation gaps) and how each was reviewed,
  tested, and resolved.
