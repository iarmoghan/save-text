"""Utilities for writing text files with sensible defaults."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Union

__all__ = ["save_text", "save_text_lines"]

PathLike = Union[str, Path]


def _prepare_path(path: PathLike) -> Path:
    path = Path(path)
    if path.parent != Path():
        path.parent.mkdir(parents=True, exist_ok=True)
    return path


def save_text(
    text: str,
    path: PathLike,
    *,
    encoding: str = "utf-8",
    append: bool = False,
    ensure_trailing_newline: bool = False,
) -> Path:
    """Write *text* to *path*.

    Parameters
    ----------
    text:
        The string content that should be written.
    path:
        The file path to write to. Parent directories are created automatically.
    encoding:
        Encoding used when writing the file. Defaults to UTF-8.
    append:
        When ``True`` the text is appended to the file instead of overwriting it.
    ensure_trailing_newline:
        When ``True`` a trailing newline is appended if the provided text does not
        already end with one.

    Returns
    -------
    pathlib.Path
        The path to the written file.
    """

    file_path = _prepare_path(path)
    content = text
    if ensure_trailing_newline and not content.endswith("\n"):
        content += "\n"

    mode = "a" if append else "w"
    with file_path.open(mode, encoding=encoding, newline="") as file:
        file.write(content)

    return file_path


def save_text_lines(
    lines: Iterable[str],
    path: PathLike,
    *,
    encoding: str = "utf-8",
    append: bool = False,
    newline: str = "\n",
    ensure_trailing_newline: bool = True,
) -> Path:
    """Write an iterable of *lines* to *path*.

    Each line is joined using *newline*. By default a trailing newline is added
    to the end of the file.
    """

    joined = newline.join(lines)
    return save_text(
        joined,
        path,
        encoding=encoding,
        append=append,
        ensure_trailing_newline=ensure_trailing_newline,
    )

