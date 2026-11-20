# Prompt Log

This file documents the specific prompts used to guide the AI assistant
(Claude, via Claude Code) through building the Flashcard Quizzer CLI, in
the order the work was actually done. Each entry follows the
Decompose -> Generate -> Review -> Refine -> Verify workflow described in
the project brief. See `docs/ai_edit_log.md` for the detailed review/
refinement notes on specific interactions.

---

## Phase 0: Requirements decomposition

**Prompt:**
> We need a lightweight internal CLI tool -- a "Flashcard Quizzer" -- to
> help new hires memorize our server acronyms and other glossary terms. It
> has to run in a terminal, load its data from JSON, support a few
> different quiz modes, and be clean enough that we can extend it later
> (e.g., a spaced-repetition mode down the road). Here's the full spec;
> I want you to turn it into a module plan before writing any code.
>
> **Functional requirements**
> - *Data ingestion:* Load flashcards from a JSON file. Validate the
>   structure. Support two shapes: a bare array of card objects
>   (`[{"front": ..., "back": ...}, ...]`) and an object wrapper
>   (`{"cards": [...]}`). If the file is missing or malformed, the app must
>   crash gracefully with a helpful, human-readable error message -- never
>   a raw Python stack trace.
> - *The quiz loop:* Present the "front" of a card, accept typed text as
>   the answer, compare it to the "back" case-insensitively, and give
>   immediate Correct/Incorrect feedback.
> - *Quiz modes:* Sequential (cards 1 through N in file order); Random
>   (shuffle the deck); Adaptive -- the challenge feature -- which must
>   prioritize cards the user previously got wrong, and must still
>   terminate even if a card is repeatedly missed.
> - *Session stats:* At the end of a quiz, show a summary: total questions
>   asked, accuracy percentage, and the list of terms the user missed.
>
> **Technical requirements**
> - *Architecture:* No single `main.py` dump -- the code must be modular
>   with real separation of concerns (something like a data-loading
>   module, a quiz-engine module, a UI/presentation module, and a thin CLI
>   entry point).
> - *Design patterns:* Use the Strategy pattern for the quiz modes, since
>   Sequential/Random/Adaptive are just different algorithms for the same
>   task (picking the next card) -- this should let us add a "spaced
>   repetition" mode later without touching the quiz loop. Use a Factory
>   to turn the user's `--mode` choice into the right strategy instance,
>   rather than an if/elif chain.
> - *Type safety:* Every function needs Python type hints.
> - *Testing:* A `pytest` suite with at least 80% code coverage, including
>   (at minimum) `test_flashcard_loader.py` with
>   `test_load_valid_flashcards_array`, `test_load_invalid_json`, and
>   `test_load_missing_required_field`; `test_quiz_modes.py` with
>   `test_quiz_mode_factory` and `test_adaptive_mode_behavior` (does it
>   actually repeat incorrect questions?); and `test_integration.py` with
>   `test_full_session` (simulate answering 3 questions and check the
>   final stats calculation).
>
> **CLI behavior**
> - `argparse` flags: `-f`/`--file`, `-m`/`--mode`, and `--stats`.
> - Colored terminal feedback: green for correct, red for incorrect.
> - The user can type "exit" or press Ctrl+C at any point and the app
>   exits cleanly, no traceback.
> - It must be runnable as `python main.py --help` and
>   `python main.py --mode sequential --file data/glossary.json`, and a
>   full adaptive game via
>   `python main.py -m adaptive -f data/python_basics.json` needs to be
>   playable start to finish.
>
> **Environment & quality gates**
> - Python 3.10+, plain `pip` + `venv` (no Poetry/Pipenv).
> - Before calling anything done, run `pytest`, `black`, `flake8`, and
>   `mypy` and make sure they're all clean -- `flake8` in particular must
>   report zero linting errors.
>
> **Deliverables**
> - The source code (modular, as above), a `tests/` directory with
>   passing tests and a coverage report demonstrating >80%, a `prompts.md`
>   prompt log documenting exactly what we asked you for at each step, a
>   `README.md` with install/run instructions, a `docs/ai_edit_log.md`
>   with at least 5 detailed examples of AI-generated code we reviewed and
>   corrected, and a final project report (1000-1500 words) reflecting on
>   the AI collaboration process.
>
> Don't write any code yet -- just give me the module plan: what files
> the app needs, what each one owns, and specifically where the Strategy
> and Factory patterns for the quiz modes are going to live.

**Outcome:** Settled on a five-module layout: `flashcard.py` (data model +
exception type), `utils/file_handler.py` (JSON loading/validation, matching
the starter repo's existing `utils/` convention), `quiz_engine.py`
(`QuizMode` ABC + `SequentialMode`/`RandomMode`/`AdaptiveMode` + a
`QuizModeFactory` + `QuizSession` for scoring), `ui.py` (pure string
formatters + thin print wrappers, for testability), and `main.py`
(argparse CLI + orchestration). This becomes the basis for every prompt
below -- each later phase drills into one module from this plan rather
than re-explaining the requirements that produced it.

---

## Phase 1: Data layer & validation

**Prompt:**
> Implement `utils/file_handler.py::load_flashcards(file_path)`. It must
> accept two JSON shapes: a bare array of `{"front", "back"}` objects, and
> `{"cards": [...]}`. Any failure -- missing file, invalid JSON syntax,
> missing "front"/"back", empty deck, wrong types -- must raise a single
> custom exception (`FlashcardDataError`) with a message a non-programmer
> could read. No `FileNotFoundError` or `json.JSONDecodeError` should ever
> reach the caller. Give me type hints on everything.

**Outcome:** Generated `flashcard.py` (the `Flashcard` dataclass and
`FlashcardDataError`) and `utils/file_handler.py` with `_read_file`,
`_parse_json`, `_extract_card_list`, and `_to_flashcard` as small private
helpers, each translating one failure mode into a `FlashcardDataError`.
Reviewed against the checklist in `ai_guidance/code_review_checklist.md`
(from the starter repo) -- see AI Edit Log Entry 1 for what got corrected.

---

## Phase 2: Quiz engine (Strategy + Factory)

**Prompt:**
> Now `quiz_engine.py`. Define an abstract `QuizMode` with `has_next()` /
> `next_card()` / `record_result(card, correct)`. Implement
> `SequentialMode` (file order), `RandomMode` (shuffle once), and
> `AdaptiveMode` (requeue wrong answers so they come back around). Adaptive
> mode needs to actually terminate -- a card that's wrong forever can't
> loop the session forever. Then a `QuizModeFactory.create(mode_name,
> cards)` that maps the `--mode` CLI string to the right class, and a
> `QuizSession` that owns scoring: case-insensitive comparison, total
> asked, correct count, and a de-duplicated ordered list of missed terms.

**Outcome:** Generated the Strategy hierarchy and factory as described.
The first draft of `AdaptiveMode` requeued a wrong card unconditionally,
which meant a card the user could never get right would quiz forever --
flagged during review and fixed with a `MAX_ATTEMPTS = 3` cap (see AI Edit
Log Entry 2).

---

## Phase 3: CLI & interaction

**Prompt:**
> Build `main.py` with `argparse`: `-f/--file` (default
> `data/glossary.json`), `-m/--mode` (choices pulled from
> `QuizModeFactory.available_modes()`, default `sequential`), and `--stats`
> for a verbose missed-terms breakdown. The quiz loop needs to accept
> "exit" (case-insensitive) or Ctrl+C/EOF without a traceback, print
> green/red feedback per answer via `ui.py`, and print the summary table
> every time the session ends -- including early exits. Structure it so
> `run_quiz()` takes an injectable `input_func` parameter, so it's testable
> without touching real stdin.

**Outcome:** Generated `main.py` and `ui.py` (colorama-backed, with pure
`format_*` functions separated from `print_*` wrappers for testability).
Initial version wired `input_func=input` as a default *parameter value* in
`run_quiz`, which broke test monkeypatching of `builtins.input` -- caught
during test-writing and fixed by passing `input_func=input` explicitly at
the `main()` call site instead (AI Edit Log Entry 3).

---

## Phase 4: Test suite

**Prompt:**
> Write the pytest suite across `tests/test_flashcard_loader.py`,
> `tests/test_quiz_modes.py`, `tests/test_integration.py`, plus
> `test_flashcard.py`, `test_ui.py`, and `test_cli.py` for full coverage.
> Cover the specific scenarios called out in the brief: valid array/object
> loads, invalid JSON, missing required fields, the factory returning the
> right class per mode name, adaptive mode actually repeating a wrong
> card, and a 3-question integration run with a final stats check. Target
> >80% coverage with `pytest --cov=. --cov-report=html`.

**Outcome:** 73 tests generated across 6 files. First run: 71 passed, 2
failed (`test_main_runs_full_quiz_successfully`,
`test_main_handles_keyboard_interrupt_at_top_level`) -- this is what
surfaced the `input_func` binding bug from Phase 3 (AI Edit Log Entry 3).
After the fix, full suite passes at 96.8% coverage.

---

## Phase 5: Quality gates

**Prompt:**
> Run `black`, `isort`, `flake8`, and `mypy` over the whole project and fix
> whatever they flag. Don't relax a rule just to make it pass unless you
> can justify why in the log.

**Outcome:** `black`/`isort` reformatted 5 files (line-length wrapping
only, no logic changes). `flake8` passed clean on the first run. `mypy`
initially reported 17 `no-untyped-def` errors, all in `tests/*` on
pytest's own fixture parameters (`capsys`, `monkeypatch`). Rather than
hand-annotate every fixture with `pytest.CaptureFixture[str]` /
`pytest.MonkeyPatch` for no functional benefit, added a scoped
`[[tool.mypy.overrides]]` for `tests.*` that disables
`disallow_untyped_defs` there only -- source modules keep full strict
typing (AI Edit Log Entry 4).

---

## Phase 6: Sample data & manual smoke test

**Prompt:**
> Create `data/glossary.json` (array format, server acronyms -- matches
> the "new hires memorize server acronyms" scenario from the ticket) and
> `data/python_basics.json` (object-wrapper format, Python syntax terms).
> Then actually run the CLI end-to-end with piped input for sequential
> mode plus `--stats`, and separately confirm a missing file and a
> malformed JSON file both fail with a clean one-line error and exit code
> 1, no traceback.

**Outcome:** Both sample files created; manual run confirmed colored
Correct/Incorrect feedback, the "exit" command ending the session early,
the summary table, and both error paths producing readable messages with
exit code 1 (AI Edit Log Entry 5).

---

## Phase 7: Rubric verification & validation

**Prompt:**
> Do one more V&V pass vs. the rubric requirements and ensure full
> compliance and completion.

**Outcome:** Wrote a small AST script to check every function in the five
source modules for a docstring -- something `flake8`/`mypy` don't catch
-- and found 18 missing (mostly one-line `has_next`/`next_card` overrides
in `quiz_engine.py` and the `print_*` wrappers in `ui.py`); fixed all of
them. Separately compared `docs/final_report.md` against the course's
`docs/report_template.md` section-by-section and found four required
sections missing entirely (Code Quality Analysis, the full Learning
Outcomes breakdown, Reflection, Appendices); rewrote the report to
include every section, backed by real metrics (`wc -l`, the AST script)
rather than estimates, then trimmed it back to the 1000-1500 word range
after adding the new content. Re-ran the full QA suite
(`pytest`/`black`/`isort`/`flake8`/`mypy`) and manually replayed the
Definition-of-Done command to confirm nothing regressed (AI Edit Log
Entry 6).
