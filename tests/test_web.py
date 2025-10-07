from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable
from urllib.parse import urlencode

import pytest

from save_text.web import SaveTextApp, _build_preview, create_app


def make_environ(path: str, method: str = "GET", data: dict[str, str] | None = None):
    from wsgiref.util import setup_testing_defaults

    environ = {}
    setup_testing_defaults(environ)
    environ["REQUEST_METHOD"] = method.upper()
    environ["PATH_INFO"] = path
    environ["HTTP_HOST"] = "example.com"
    if data is not None:
        encoded = urlencode(data).encode()
        environ["CONTENT_TYPE"] = "application/x-www-form-urlencoded"
        environ["CONTENT_LENGTH"] = str(len(encoded))
        environ["wsgi.input"] = BytesIO(encoded)
    else:
        environ["CONTENT_LENGTH"] = "0"
        environ["wsgi.input"] = BytesIO()
    return environ


def run_request(app: SaveTextApp, environ) -> tuple[str, dict[str, str], bytes]:
    headers: dict[str, str] = {}

    def start_response(status: str, response_headers: Iterable[tuple[str, str]]):
        headers.update(response_headers)
        headers["status"] = status

    body = b"".join(app(environ, start_response))
    return headers["status"], headers, body


@pytest.fixture()
def app(tmp_path: Path) -> SaveTextApp:
    database = tmp_path / "pastes.sqlite3"
    return create_app(database)


def test_create_and_view_paste(app: SaveTextApp):
    status, headers, _ = run_request(app, make_environ("/p", "POST", {"content": "Hello web"}))
    assert status.startswith("302")
    detail_path = headers["Location"].split("example.com")[-1]

    status, _, body = run_request(app, make_environ(detail_path))
    assert status.startswith("200")
    assert b"Hello web" in body

    status, _, list_body = run_request(app, make_environ("/pastes"))
    assert status.startswith("200")
    assert b"Hello web" in list_body


def test_delete_paste_removes_entry(app: SaveTextApp):
    _, headers, _ = run_request(app, make_environ("/p", "POST", {"content": "Temporary"}))
    detail_path = headers["Location"].split("example.com")[-1]
    slug = detail_path.rsplit("/", 1)[-1]

    status, headers, _ = run_request(app, make_environ(f"/p/{slug}/delete", "POST"))
    assert status.startswith("302")
    assert headers["Location"].endswith("/pastes?message=deleted")

    status, _, body = run_request(app, make_environ(detail_path))
    assert status.startswith("404")
    assert b"Not found" in body


@pytest.mark.parametrize(
    "text,expected",
    [
        ("single line", "single line"),
        ("lots of whitespace\n\n\n spaced", "lots of whitespace spaced"),
        ("x" * 200, "x" * 159 + "\u2026"),
    ],
)
def test_build_preview(text: str, expected: str):
    assert _build_preview(text) == expected
