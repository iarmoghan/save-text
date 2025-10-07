# Save Text

Static pastebin-style interface that works entirely in the browser. The site ships as
plain HTML, CSS, and JavaScript so it can be hosted on GitHub Pages (or any other
static file host) without additional services.

## Features

- Create text pastes directly in your browser.
- Generate a link to reopen the paste later.
- Browse all saved pastes in a responsive card layout.
- Delete pastes to remove them from your saved list and invalidate their links.

All data lives in `localStorage`, so pastes stay on the device where they were
created. This keeps the project compatible with GitHub Pages, which cannot run
server-side code.

## Local development

Open the HTML files in any modern browser. For example:

```bash
python -m http.server --directory docs
```

Visit `http://localhost:8000/docs/index.html` to create pastes and
`http://localhost:8000/docs/saved.html` to review them.

## Deploying on GitHub Pages

1. Commit the contents of the `docs/` directory to your repository.
2. In your repository settings, enable GitHub Pages and choose the **Deploy from a
   branch** option.
3. Select your default branch and the `/docs` folder as the publishing source.
4. Wait for Pages to build, then share the published URL.

Because the experience runs entirely in the browser, no build steps or backend
services are required.
