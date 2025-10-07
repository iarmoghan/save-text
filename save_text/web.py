"""A small WSGI application that mimics a paste service."""

from __future__ import annotations

import html
import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Callable, Iterable, Iterator, Optional
from urllib.parse import parse_qs, urlencode

DEFAULT_DATABASE = Path(__file__).with_name("pastes.sqlite3")
STATIC_DIR = Path(__file__).with_name("static")


def create_app(database_path: Optional[Path] = None) -> "SaveTextApp":
    return SaveTextApp(database_path or DEFAULT_DATABASE)


def main() -> None:
    from wsgiref.simple_server import make_server

    app = create_app()
    host = "0.0.0.0"
    port = 8000
    with make_server(host, port, app) as server:
        print(f"Serving on http://{host}:{port}")
        server.serve_forever()


@dataclass
class Paste:
    slug: str
    content: str
    preview: str
    created_at: datetime


class SaveTextApp:
    def __init__(self, database_path: Path):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    # -- WSGI interface -------------------------------------------------
    def __call__(self, environ, start_response: Callable):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = environ.get("PATH_INFO", "") or "/"
        query_string = environ.get("QUERY_STRING", "")
        query = {key: values for key, values in parse_qs(query_string).items()}

        if method == "GET" and path == "/":
            body = self._render_home(query)
            return self._respond(start_response, "200 OK", body)

        if method == "GET" and path == "/pastes":
            body = self._render_saved(query)
            return self._respond(start_response, "200 OK", body)

        if method == "GET" and path == "/static/style.css":
            return self._respond_file(start_response, "200 OK", "text/css", STATIC_DIR / "style.css")

        if method == "POST" and path == "/p":
            form = self._parse_form(environ)
            content = form.get("content", "").strip()
            if not content:
                location = self._build_url(environ, "/", {"error": "empty"})
                return self._respond(start_response, "302 Found", b"", [("Location", location)])

            slug = self._create_paste(content)
            location = self._build_url(environ, f"/p/{slug}")
            return self._respond(start_response, "302 Found", b"", [("Location", location)])

        if method == "GET" and path.startswith("/p/"):
            slug = path.removeprefix("/p/")
            paste = self._get_paste(slug)
            if paste is None:
                return self._respond_not_found(start_response)
            body = self._render_paste(paste, environ, query)
            return self._respond(start_response, "200 OK", body)

        if method == "POST" and path.startswith("/p/") and path.endswith("/delete"):
            slug = path.split("/")[-2]
            if self._delete_paste(slug):
                location = self._build_url(environ, "/pastes", {"message": "deleted"})
                return self._respond(start_response, "302 Found", b"", [("Location", location)])
            return self._respond_not_found(start_response)

        return self._respond_not_found(start_response)

    # -- Rendering ------------------------------------------------------
    def _render_home(self, query: dict[str, list[str]]) -> bytes:
        message = ""
        if query.get("error") == ["empty"]:
            message = "<p class=\"flash\">Please paste some text before creating a link.</p>"

        body = f"""
        <section class=\"panel\">
          <h2>Create a new paste</h2>
          {message}
          <form action=\"/p\" method=\"post\" class=\"paste-form\">
            <label for=\"content\">Paste your text below:</label>
            <textarea id=\"content\" name=\"content\" rows=\"12\" placeholder=\"Start typing or paste your text here...\" required></textarea>
            <button type=\"submit\" class=\"primary\">Create new text</button>
          </form>
        </section>
        """
        return self._layout("Create Paste", body)

    def _render_saved(self, query: dict[str, list[str]]) -> bytes:
        message = ""
        if query.get("message") == ["deleted"]:
            message = "<p class=\"flash\">Paste deleted.</p>"

        cards = "".join(self._render_card(paste) for paste in self._query_pastes())
        content = (
            "<div class=\"paste-grid\">" + cards + "</div>"
            if cards
            else "<p>You have not saved any pastes yet. <a href=\"/\">Create your first paste.</a></p>"
        )

        body = f"""
        <section class=\"panel\">
          <h2>Saved pastes</h2>
          {message}
          {content}
        </section>
        """
        return self._layout("Saved Pastes", body)

    def _render_card(self, paste: Paste) -> str:
        preview = html.escape(paste.preview)
        created = paste.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        return f"""
        <article class=\"paste-card\">
          <h3><a href=\"/p/{paste.slug}\">{paste.slug}</a></h3>
          <p class=\"preview\">{preview}</p>
          <p class=\"meta\">{created}</p>
          <form action=\"/p/{paste.slug}/delete\" method=\"post\">
            <button type=\"submit\" class=\"danger\">Delete</button>
          </form>
        </article>
        """

    def _render_paste(self, paste: Paste, environ, query: dict[str, list[str]]) -> bytes:
        message = ""
        if query.get("message") == ["deleted"]:
            message = "<p class=\"flash\">Paste deleted.</p>"

        created = paste.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        base_url = self._base_url(environ)
        link = f"{base_url}/p/{paste.slug}"
        escaped = html.escape(paste.content)

        body = f"""
        <section class=\"panel\">
          <header class=\"panel-header\">
            <div>
              <h2>Saved paste</h2>
              <p class=\"meta\">Link: <a href=\"{link}\">{link}</a></p>
              <p class=\"meta\">Created {created}</p>
            </div>
            <form action=\"/p/{paste.slug}/delete\" method=\"post\">
              <button type=\"submit\" class=\"danger\">Delete paste</button>
            </form>
          </header>
          {message}
          <pre class=\"paste-content\"><code>{escaped}</code></pre>
        </section>
        """
        return self._layout(f"Paste {paste.slug}", body)

    def _layout(self, title: str, body: str) -> bytes:
        css_link = "<link rel=\"stylesheet\" href=\"/static/style.css\">"
        markup = f"""<!doctype html>
<html lang=\"en\">
  <head>
    <meta charset=\"utf-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <title>{html.escape(title)} · Save Text</title>
    {css_link}
  </head>
  <body>
    <header class=\"site-header\">
      <div class=\"container\">
        <h1 class=\"site-title\"><a href=\"/\">Save Text</a></h1>
        <nav>
          <a href=\"/\">Create Paste</a>
          <a href=\"/pastes\">Saved Pastes</a>
        </nav>
      </div>
    </header>
    <main class=\"container\">
      {body}
    </main>
    <footer class=\"site-footer\">
      <div class=\"container\">
        <p>Built without external dependencies. Paste, save, and revisit your text snippets.</p>
      </div>
    </footer>
  </body>
</html>"""
        return markup.encode("utf-8")

    # -- Responses ------------------------------------------------------
    def _respond(
        self,
        start_response: Callable,
        status: str,
        body: bytes,
        extra_headers: Optional[list[tuple[str, str]]] = None,
    ) -> Iterable[bytes]:
        headers = [("Content-Type", "text/html; charset=utf-8"), ("Content-Length", str(len(body)))]
        if extra_headers:
            headers.extend(extra_headers)
        start_response(status, headers)
        return [body]

    def _respond_file(self, start_response: Callable, status: str, content_type: str, path: Path) -> Iterable[bytes]:
        if not path.exists():
            return self._respond_not_found(start_response)
        data = path.read_bytes()
        headers = [("Content-Type", content_type), ("Content-Length", str(len(data)))]
        start_response(status, headers)
        return [data]

    def _respond_not_found(self, start_response: Callable) -> Iterable[bytes]:
        body = self._layout("Not found", "<section class=\"panel\"><h2>Not found</h2><p>The requested paste could not be located.</p></section>")
        return self._respond(start_response, "404 Not Found", body)

    # -- Database helpers -----------------------------------------------
    def _ensure_schema(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS paste (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    slug TEXT NOT NULL UNIQUE,
                    content TEXT NOT NULL,
                    preview TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_paste(self, content: str) -> str:
        preview = _build_preview(content)
        slug = self._generate_unique_slug()
        created_at = datetime.utcnow().isoformat(timespec="seconds")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO paste (slug, content, preview, created_at) VALUES (?, ?, ?, ?)",
                (slug, content, preview, created_at),
            )
            connection.commit()
        return slug

    def _get_paste(self, slug: str) -> Optional[Paste]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT slug, content, preview, created_at FROM paste WHERE slug = ?",
                (slug,),
            ).fetchone()
        if row is None:
            return None
        return Paste(
            slug=row["slug"],
            content=row["content"],
            preview=row["preview"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _query_pastes(self) -> Iterator[Paste]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT slug, content, preview, created_at FROM paste ORDER BY created_at DESC"
            ).fetchall()
        for row in rows:
            yield Paste(
                slug=row["slug"],
                content=row["content"],
                preview=row["preview"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )

    def _delete_paste(self, slug: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute("DELETE FROM paste WHERE slug = ?", (slug,))
            connection.commit()
        return cursor.rowcount > 0

    def _generate_unique_slug(self) -> str:
        while True:
            candidate = secrets.token_urlsafe(6)
            with self._connect() as connection:
                exists = connection.execute(
                    "SELECT 1 FROM paste WHERE slug = ?",
                    (candidate,),
                ).fetchone()
            if exists is None:
                return candidate

    # -- Utilities ------------------------------------------------------
    def _parse_form(self, environ) -> dict[str, str]:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            length = 0
        body = environ.get("wsgi.input", BytesIO()).read(length)
        data = body.decode("utf-8") if body else ""
        parsed = parse_qs(data)
        return {key: values[0] for key, values in parsed.items()}

    def _build_url(self, environ, path: str, params: Optional[dict[str, str]] = None) -> str:
        scheme = environ.get("wsgi.url_scheme", "http")
        host = environ.get("HTTP_HOST") or environ.get("SERVER_NAME", "localhost")
        query = f"?{urlencode(params)}" if params else ""
        return f"{scheme}://{host}{path}{query}"

    def _base_url(self, environ) -> str:
        scheme = environ.get("wsgi.url_scheme", "http")
        host = environ.get("HTTP_HOST") or environ.get("SERVER_NAME", "localhost")
        return f"{scheme}://{host}"


def _build_preview(content: str, *, limit: int = 160) -> str:
    condensed = " ".join(content.split())
    if len(condensed) <= limit:
        return condensed
    return condensed[: limit - 1] + "\u2026"


__all__ = ["SaveTextApp", "create_app", "main", "_build_preview"]


if __name__ == "__main__":  # pragma: no cover
    main()
