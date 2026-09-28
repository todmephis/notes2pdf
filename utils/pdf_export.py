"""Genera el PDF final combinando markdown + tema + color de acento."""
import os

from flask import render_template
from pygments.formatters import HtmlFormatter
from weasyprint import HTML

from .md_render import render_markdown_to_html

THEMES_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "themes")

PAGE_SIZES = {"A4": "A4", "Carta": "letter"}


def available_themes() -> list[str]:
    return sorted(
        os.path.splitext(f)[0]
        for f in os.listdir(THEMES_DIR)
        if f.endswith(".css")
    )


def _read_theme_css(theme: str) -> str:
    path = os.path.join(THEMES_DIR, f"{theme}.css")
    if not os.path.isfile(path):
        raise ValueError(f"Tema desconocido: {theme}")
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_pdf(
    markdown_text: str,
    base_dir: str,
    title: str,
    theme: str = "minimal",
    accent_color: str = "#2563eb",
    page_size: str = "A4",
) -> bytes:
    content_html = render_markdown_to_html(markdown_text)
    theme_css = _read_theme_css(theme)
    pygments_css = HtmlFormatter(style="friendly").get_style_defs(".highlight")

    full_html = render_template(
        "pdf_base.html",
        title=title,
        content=content_html,
        theme_css=theme_css,
        pygments_css=pygments_css,
        accent_color=accent_color,
        page_size=PAGE_SIZES.get(page_size, "A4"),
    )

    return HTML(string=full_html, base_url=base_dir).write_pdf()
