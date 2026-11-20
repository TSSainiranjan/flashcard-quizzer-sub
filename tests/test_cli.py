"""Tests for main.py's argparse configuration and top-level main()
orchestration, including graceful handling of bad files and Ctrl+C.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from main import build_arg_parser, main


class TestArgParser:
    def test_defaults(self) -> None:
        args = build_arg_parser().parse_args([])
        assert args.file == "data/glossary.json"
        assert args.mode == "sequential"
        assert args.stats is False

    def test_custom_flags(self) -> None:
        args = build_arg_parser().parse_args(
            ["-f", "data/python_basics.json", "-m", "adaptive", "--stats"]
        )
        assert args.file == "data/python_basics.json"
        assert args.mode == "adaptive"
        assert args.stats is True

    def test_invalid_mode_choice_exits(self) -> None:
        with pytest.raises(SystemExit):
            build_arg_parser().parse_args(["-m", "not-a-real-mode"])

    def test_help_flag_exits_cleanly(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc_info:
            build_arg_parser().parse_args(["--help"])
        assert exc_info.value.code == 0
        out = capsys.readouterr().out
        assert "--file" in out
        assert "--mode" in out
        assert "--stats" in out


class TestMainErrorHandling:
    def test_main_reports_missing_file_without_traceback(self, capsys) -> None:
        exit_code = main(["-f", "does/not/exist.json"])

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Traceback" not in captured.out
        assert "Traceback" not in captured.err
        assert "Error" in captured.out

    def test_main_reports_malformed_json_without_traceback(
        self, tmp_path: Path, capsys
    ) -> None:
        bad_file = tmp_path / "broken.json"
        bad_file.write_text("{not json", encoding="utf-8")

        exit_code = main(["-f", str(bad_file)])

        assert exit_code == 1
        assert "Traceback" not in capsys.readouterr().out

    def test_main_runs_full_quiz_successfully(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        data_file = tmp_path / "deck.json"
        data_file.write_text(
            '[{"front": "CPU", "back": "Central Processing Unit"}]',
            encoding="utf-8",
        )

        monkeypatch.setattr(
            "builtins.input", lambda _prompt="": "Central Processing Unit"
        )

        exit_code = main(["-f", str(data_file), "-m", "sequential"])

        assert exit_code == 0
        assert "Quiz Summary" in capsys.readouterr().out

    def test_main_handles_keyboard_interrupt_at_top_level(
        self, tmp_path: Path, monkeypatch, capsys
    ) -> None:
        data_file = tmp_path / "deck.json"
        data_file.write_text(
            '[{"front": "CPU", "back": "Central Processing Unit"}]',
            encoding="utf-8",
        )

        def _raise_interrupt(_prompt: str = "") -> str:
            raise KeyboardInterrupt

        monkeypatch.setattr("builtins.input", _raise_interrupt)

        exit_code = main(["-f", str(data_file)])

        assert exit_code == 0
        assert "Goodbye" in capsys.readouterr().out
