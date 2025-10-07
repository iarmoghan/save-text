# save-text

`save-text` is a lightweight Python utility for persisting text content to disk. It now also includes a minimal web application for capturing pastes, browsing saved snippets, and deleting them when they are no longer needed. The project provides helper functions, a command line interface, and a friendly browser experience for saving strings while ensuring parent directories exist — all without external web frameworks.

## Installation

```
pip install .
```

To install the optional development dependencies run:

```
pip install .[dev]
```

## Usage

### Python API

```python
from save_text import save_text, save_text_lines

# Write a single string
save_text("Hello, world!", "output/message.txt")

# Append multiple lines with a trailing newline
save_text_lines(["first", "second"], "output/list.txt", append=True)
```

### Command line interface

```
save-text path/to/file.txt "Some content" "Another line"
```

Use `--append` to append to an existing file, or `--stdin` to read from standard input:

```
echo "Hello" | save-text output/from-stdin.txt --stdin
```

### Web application

Launch the built-in web interface to paste and manage saved texts:

```
python -m save_text.web
```

The home page provides a large text area. Paste your text and click **Create new text** to generate a unique link. Use the **Saved Pastes** menu to review all stored snippets in card form, open any of them, or delete entries you no longer need.

## Development

Run the tests with:

```
pytest
```
