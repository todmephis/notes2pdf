# Notes → PDF

A Flask app that converts Notion or Obsidian exports (Markdown) into styled PDFs, with a live in-browser preview, multiple themes, and fine-grained control over colors, headers/footers, and watermarks.

## Features

- **Notion and Obsidian support**: pick the source platform in the form. Accepts a plain `.md` file or a `.zip` (Notion export with images/subpages, or an Obsidian note/vault with its attachments folder). Zip files are extracted safely (no path traversal) and images are resolved automatically. For Obsidian, wikilinks and embeds (`[[Note]]`, `![[image.png]]`) are converted to standard Markdown, YAML frontmatter is stripped, and attachments are found even if they live in a shared folder instead of next to the note.
- **Live preview**: the right-hand panel renders the actual PDF (not an approximation) and updates automatically, with debouncing, as you change any option.
- **7 built-in themes**: `minimal`, `dark`, `academic`, `github`, `sepia`, `terminal`, and `notion` (replicates Notion's native look — signature gray text, coral inline code, unstyled headings). Themes live in `static/themes/*.css` and are auto-discovered.
- **Configurable accent color**, applied to headings/links/borders depending on the theme. Switching themes suggests that theme's default accent, which you can still override.
- **Page size**: A4 or Letter.
- **Header, footer, and page numbers**: optional text repeated on every page (top and bottom), plus automatic "Page X of Y" numbering — implemented with CSS Paged Media `@page` margin boxes.
- **Watermark**: text or image, with adjustable opacity and size, repeated on every page via a `position: fixed` overlay.
- **Code color customization**: override the background/text color of code blocks (` ``` `) and inline code (`` ` ``) independently, or use the same colors for both.
- **Bilingual UI**: English by default, with a Spanish toggle in the settings menu (top right). Backend error messages are localized too.
- **Dark/light UI mode**, independent of the PDF theme, toggled from the same settings menu.

## Requirements

- Python 3.11+
- Homebrew (macOS) with WeasyPrint's native libraries:

```bash
brew install pango gdk-pixbuf libffi
```

## Install

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open http://127.0.0.1:5050

## Project structure

```
app.py                       # Flask routes: / (form), /convert (download), /preview (live preview)
templates/
  index.html                   # web form, settings menu, live preview panel, i18n + theme JS
  pdf_base.html                  # base HTML wrapping the converted markdown for WeasyPrint
static/themes/                   # CSS themes (auto-discovered): minimal, dark, academic, github, sepia, terminal, notion
utils/
  notion_import.py                 # safe .md / .zip extraction, shared by both source platforms
  obsidian_import.py                 # Obsidian-only preprocessing: wikilinks, embeds, frontmatter, asset lookup
  md_render.py                         # Markdown -> HTML conversion
  pdf_export.py                          # builds the final HTML (theme + watermark + code colors + header/footer) and renders the PDF
  i18n.py                                  # backend error message translations (en/es)
```

## Adding a new theme

Drop a new `.css` file in `static/themes/`; it will appear in the theme dropdown automatically (using the filename, capitalized). To stay consistent with the customization options, a theme should:

- Use `var(--accent, <fallback>)` for headings/links/borders.
- Use `var(--block-code-bg, <fallback>)` / `var(--block-code-text, <fallback>)` on `pre`.
- Use `var(--inline-code-bg, <fallback>)` / `var(--inline-code-text, <fallback>)` on `code`.
- Set `white-space: pre-wrap; overflow-wrap: anywhere;` on `pre` — WeasyPrint has no horizontal scroll, so long lines must wrap instead of overflowing.
- If the theme uses a non-white page background, add `@page { background: ... }` so the color fills the full page margins, not just the content box.
