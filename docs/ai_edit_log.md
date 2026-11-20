# AI Edit Log

This log documents specific AI interactions during the build of the
Flashcard Quizzer CLI, following the template from the course starter
repo. It focuses on the moments where AI-generated code was reviewed,
tested, and corrected -- not just accepted as-is. See `prompts.md` for
the full prompt sequence these entries are drawn from.

---

## Entry 1 - 2026-11-20 - Data loader error taxonomy

**Context:** The functional spec requires that a missing or malformed
JSON file "crash gracefully with a helpful error message, not a stack
trace." That means every place `json.loads()` or `open()` can fail needs
to be caught and re-raised as something readable.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Implement `load_flashcards()` supporting both array
and `{"cards": [...]}` formats. Every failure mode must raise
`FlashcardDataError` with a human-readable message -- no raw
`FileNotFoundError` or `json.JSONDecodeError` should reach the caller."

**AI Response:** Claude generated `_read_file`, `_parse_json`,
`_extract_card_list`, and `_to_flashcard` as separate helpers, each
translating exactly one failure mode into `FlashcardDataError`.

**Changes Made:**
- Added an explicit empty-deck check (`No flashcards found in '...'`) --
  the first draft would have silently produced a `QuizMode` with an
  empty card list, which `QuizMode.__init__` then rejects with a less
  useful generic `ValueError`.
- Added per-field validation that `front`/`back` are non-empty strings
  (not just "key present"), since a card with `"back": ""` would let a
  blank answer be scored as correct.
- Included the line/column number from `json.JSONDecodeError` in the
  friendly message so a user with a typo doesn't have to guess where it
  is.

**Reasoning:** The spec's bar is "helpful error message," not just "no
traceback." A message that says "invalid JSON" without a location isn't
much better than a traceback for someone trying to fix their own data
file.

**Outcome:** `test_flashcard_loader.py` has 15 tests covering every
branch of this module; coverage on `utils/file_handler.py` is 99% (the
one uncovered line is an `OSError` branch for permission-denied-style
failures that aren't practical to trigger portably in a test).

**Lessons Learned:** AI-generated error handling tends to stop at "catch
the exception" -- it takes an explicit prompt (and a review pass against
the "Error Handling" section of `ai_guidance/code_review_checklist.md`)
to push it to "catch the exception *and* make the message actually
actionable."

---

## Entry 2 - 2026-11-20 - AdaptiveMode could loop forever

**Context:** The Adaptive quiz mode is described in the spec as "the
challenge feature" -- it must reprioritize cards the user gets wrong.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Implement `AdaptiveMode` so a wrong answer requeues
the card to come back around later in the session."

**AI Response:** The first generated version reinserted a wrong card back
into the queue unconditionally on every incorrect answer, with no upper
bound.

**Changes Made:** Added a `MAX_ATTEMPTS = 3` class constant and an
`_attempts` dict keyed by `card.front`. A card is only requeued while
`attempts < MAX_ATTEMPTS`; past that it's dropped (and already recorded
in `QuizSession`'s missed-terms list from its first wrong answer).

**Reasoning:** A deck where the user is stuck on one term forever would
turn "adaptive quizzing" into "the app never ends," which is a real
usability bug, not just an edge case. Capping attempts keeps the
prioritization behavior (wrong cards *do* come back sooner) while
guaranteeing the session always terminates.

**Outcome:** Wrote
`test_adaptive_mode_drops_card_after_max_attempts`, which drives a
single-card deck to failure repeatedly and asserts the loop stops at
exactly `MAX_ATTEMPTS` attempts -- this test would have hung (well,
run 50+ iterations without terminating, per the test's own safety cap)
against the original unbounded implementation.

**Lessons Learned:** "Prioritize wrong cards" is an underspecified
requirement -- an AI (or a human) implementing it literally will produce
something that's technically correct and practically broken. Termination
conditions for any kind of retry/requeue logic need to be called out
explicitly in the prompt, or checked for explicitly in review.

---

## Entry 3 - 2026-11-20 - Monkeypatched `input` wasn't taking effect

**Context:** While writing `tests/test_cli.py`, two tests that
monkeypatch `builtins.input` and call `main()` failed with
`OSError: pytest: reading from stdin while output is captured!`, meaning
the real `input()` was still being invoked despite the patch.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** (Debugging prompt, following the pattern from
`ai_guidance/prompting_best_practices.md`) "These two tests monkeypatch
`builtins.input` but `main()` still reads real stdin. Here's the
traceback and the relevant code in `main.py` and `run_quiz`. Why isn't
the patch taking effect?"

**AI Response:** Identified the root cause: `run_quiz`'s signature was
`def run_quiz(..., input_func: Callable[[str], str] = input, ...)`. A
default parameter value is evaluated exactly once, at function
*definition* time (module import), so `input_func` was bound to the
original `builtins.input` object before any test ever ran --
`monkeypatch.setattr("builtins.input", ...)` patches the name `input` in
the `builtins` module, which doesn't retroactively change an already-bound
default argument.

**Changes Made:** In `main()`, changed the call from
`run_quiz(cards, args.mode, show_detailed_stats=args.stats)` to
`run_quiz(cards, args.mode, input_func=input, show_detailed_stats=args.stats)`.
Referencing the bare name `input` inside `main()`'s body resolves it at
*call* time via normal name lookup, which does see the monkeypatched
`builtins.input`.

**Reasoning:** `run_quiz`'s own default (`input_func=input`) is still
useful for callers other than `main()` (e.g. calling `run_quiz` directly
from a REPL or another script) -- removing the default entirely would
make the function less convenient to use standalone. The fix only needed
to change how `main()` invokes it.

**Outcome:** Both previously-failing tests
(`test_main_runs_full_quiz_successfully`,
`test_main_handles_keyboard_interrupt_at_top_level`) pass; full suite is
73/73.

**Lessons Learned:** This is a classic "mutable/late-binding default
argument" gotcha, except in reverse -- normally the danger is a *mutable*
default persisting state across calls; here the danger was an
*immutable* reference (a function object) getting captured too early to
be mockable. AI-generated code that wires up dependency injection via
default parameters needs a specific check during review: "is this
default evaluated at a time when tests can still intercept it?"

---

## Entry 4 - 2026-11-20 - Scoping a strict mypy rule to source, not tests

**Context:** Running `mypy .` after enabling `disallow_untyped_defs = true`
project-wide (per the "Definition of Done" requirement that all functions
have type hints) produced 17 errors, all in `tests/*`, all on pytest's own
injected fixture parameters (`capsys`, `monkeypatch`) which the test
functions don't explicitly type.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Should I hand-annotate every `capsys`/`monkeypatch`
parameter across the test files, or is there a better fix?"

**AI Response:** Recommended adding pytest's exact fixture types
(`pytest.CaptureFixture[str]`, `pytest.MonkeyPatch`) everywhere, but
flagged that a `[[tool.mypy.overrides]]` block scoped to `tests.*` is the
more common convention for this exact situation, since test-fixture
typing is boilerplate that doesn't catch real bugs in test code.

**Changes Made:** Added
```toml
[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```
to `pyproject.toml`, leaving strict typing enforced on every source
module (`main.py`, `ui.py`, `quiz_engine.py`, `utils/file_handler.py`,
`flashcard.py`).

**Reasoning:** The project requirement is "all functions must have Python
Type Hints" in the context of the application's own logic -- the intent
is catching real type errors in `quiz_engine.py`/`utils/file_handler.py`,
not forcing verbose annotations on every pytest fixture parameter, which
is a widely accepted mypy convention (used in mypy's own test suite,
among others).

**Outcome:** `mypy .` reports "Success: no issues found in 13 source
files" with source-level strictness fully intact.

**Lessons Learned:** Not every AI suggestion needed rejecting outright --
this one was accepted with a scope adjustment. Blindly satisfying a
linter by relaxing it everywhere is a code smell; the fix here narrows
the relaxation to exactly the files where it's justified and leaves a
comment-free but self-documenting `[[tool.mypy.overrides]]` block that
makes the scope obvious to the next reader.

---

## Entry 5 - 2026-11-20 - Manual smoke test caught a UX gap the tests missed

**Context:** All 73 automated tests passed, but automated tests alone
don't prove the interactive experience reads well in a real terminal.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Run the CLI for real: `--help`, a piped sequential
session against `data/glossary.json` with `--stats`, then a missing-file
run and a malformed-JSON run, and show me the raw output."

**AI Response:** Ran all four scenarios and reported the captured
terminal output verbatim.

**Changes Made:** No code changes were needed -- output matched
expectations (colored feedback in a real ANSI terminal, "Goodbye!" on
`exit`, the summary table appearing even after an early exit, and both
error scenarios producing a single-line `Error: ...` message with exit
code 1 and no traceback).

**Reasoning:** Verified rather than assumed. This step exists specifically
because "tests pass" and "the tool feels right to use" are different
claims -- the project's Definition of Done explicitly requires being able
to "run `python main.py -m adaptive -f data/python_basics.json` and play
a full game," which only a real run confirms.

**Outcome:** Confirmed the app meets the Definition of Done as written,
with no further changes required.

**Lessons Learned:** Even with 96%+ coverage, a manual pass has value --
it's the difference between "the functions return the values the
assertions expect" and "a new hire sitting at a terminal would find this
usable."

---

## Entry 6 - 2026-11-20 - Rubric V&V pass found missing docstrings and an incomplete report

**Context:** After the initial build was "done" (all tests passing, all
linters clean), a dedicated verification-and-validation pass was run
against `docs/project_rubric.md` line by line, rather than assuming the
earlier phases had covered everything.

**AI Tool Used:** Claude (Claude Code)

**Prompt/Request:** "Do one more V&V pass vs. the rubric requirements and
ensure full compliance and completion."

**AI Response:** Wrote a small AST-based script to walk every function
definition in the five source modules and flag any missing a docstring
-- `flake8`/`mypy` don't check for docstring presence, so this had never
been directly verified despite the rubric requiring "functions have
appropriate docstrings." It found 18 undocumented functions (`__init__`
methods and the `has_next`/`next_card`/`record_result` overrides in
`quiz_engine.py`, and all six `print_*` wrappers in `ui.py`). Separately,
comparing `docs/final_report.md` against `docs/report_template.md`
section-by-section found four entire required sections missing: Code
Quality Analysis, the three Learning Outcomes subsections (only a merged
paragraph existed), Reflection, and Appendices.

**Changes Made:** Added docstrings to all 18 flagged functions. Rewrote
`final_report.md` to include every template section with real content
(actual line counts and function counts pulled from `wc -l` and the AST
script, not estimated), then trimmed it from 1,778 words back down to
1,495 to stay within the brief's 1,000-1,500 word requirement after
adding the new sections.

**Reasoning:** A rubric with "reviewer tips" like "check that all
sections of the template are completed" is effectively a checklist a
human grader will run through line by line -- the right response is to
run through it the same way, not to re-skim the code and assume prior
phases caught everything.

**Outcome:** 0 missing docstrings (re-verified with the same AST script);
`final_report.md` now has all 12 sections from the template; full QA
suite (`pytest`, `black`, `isort`, `flake8`, `mypy`) re-run clean after
every change in this pass; the exact Definition-of-Done command
(`python main.py -m adaptive -f data/python_basics.json`) re-run manually
to confirm it still plays a full game end to end.

**Lessons Learned:** "All tests pass and the linters are clean" is not
the same claim as "every rubric line item is satisfied" -- docstring
presence and template-section completeness are both things no automated
tool in this project's toolchain checks, so they need an explicit,
separate verification pass against the actual grading document.

---

## Summary Statistics

- **Total AI interactions:** 7 (one per phase in `prompts.md`, expanded
  into 6 detailed entries above)
- **Lines of AI-generated code used:** ~950 (source + tests, across
  `flashcard.py`, `utils/file_handler.py`, `quiz_engine.py`, `ui.py`,
  `main.py`, and the six files under `tests/`)
- **Lines of AI-generated code modified:** ~60 (the `AdaptiveMode`
  termination guard, the `input_func` call-site fix, the empty-deck and
  blank-field validation additions, the mypy override, 18 added
  docstrings)
- **Most helpful AI interaction:** Phase 2 (Strategy/Factory scaffolding)
  -- turned a fairly abstract design-pattern requirement into a concrete,
  extensible class hierarchy in one pass.
- **Most challenging AI interaction:** Entry 3 (the `input_func` default-
  binding bug) -- required tracing a test failure back through Python's
  argument-evaluation semantics rather than the application logic itself.
- **Biggest lesson learned:** AI-generated code is usually correct for
  the *stated* requirement but silent on the *unstated* ones (termination
  guarantees, testability of injected dependencies, docstring coverage,
  template completeness). Catching those requires running the code and
  checking it against the actual grading criteria -- not just reading it
  or assuming "tests pass" is the finish line.
