from __future__ import annotations

import io
from pathlib import Path

import pytest

from save_text import save_text, save_text_lines
from save_text.cli import main as cli_main


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_save_text_overwrites(tmp_path: Path) -> None:
    path = tmp_path / "example.txt"
    save_text("hello", path)
    save_text("world", path)
    assert read(path) == "world"


def test_save_text_appends(tmp_path: Path) -> None:
    path = tmp_path / "example.txt"
    save_text("hello", path)
    save_text("world", path, append=True)
    assert read(path) == "helloworld"


def test_save_text_trailing_newline(tmp_path: Path) -> None:
    path = tmp_path / "example.txt"
    save_text("hello", path, ensure_trailing_newline=True)
    assert read(path) == "hello\n"


def test_save_text_lines(tmp_path: Path) -> None:
    path = tmp_path / "example.txt"
    save_text_lines(["a", "b"], path)
    assert read(path) == "a\nb\n"


def test_save_text_lines_without_trailing_newline(tmp_path: Path) -> None:
    path = tmp_path / "example.txt"
    save_text_lines(["a", "b"], path, ensure_trailing_newline=False)
    assert read(path) == "a\nb"


def test_cli_with_content_arguments(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "cli.txt"
    args = [str(path), "hello", "world"]
    assert cli_main(args) == 0
    assert read(path) == "hello\nworld\n"


def test_cli_with_stdin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "cli.txt"
    stdin = io.StringIO("hello\nworld")
    monkeypatch.setattr("sys.stdin", stdin)
    args = [str(path), "--stdin"]
    assert cli_main(args) == 0
    assert read(path) == "hello\nworld\n"


@pytest.mark.parametrize(
    "args",
    [
        ["file.txt"],
        ["file.txt", "--stdin", "content"],
    ],
)
def test_cli_argument_errors(args: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        cli_main(args)

