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


def _css_string(value: str) -> str:
    """Escapa texto para insertarlo de forma segura en un `content: "...";` de CSS."""
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ").replace("\r", "")


def build_pdf(
    markdown_text: str,
    base_dir: str,
    title: str,
    theme: str = "minimal",
    accent_color: str = "#2563eb",
    page_size: str = "A4",
    watermark_text: str | None = None,
    watermark_image_data_uri: str | None = None,
    watermark_opacity: float = 0.15,
    watermark_scale: float = 1.0,
    block_code_bg_color: str | None = None,
    block_code_text_color: str | None = None,
    inline_code_bg_color: str | None = None,
    inline_code_text_color: str | None = None,
    header_text: str | None = None,
    footer_text: str | None = None,
    page_numbers_enabled: bool = False,
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
        watermark_text=watermark_text,
        watermark_image_data_uri=watermark_image_data_uri,
        watermark_opacity=max(0.0, min(watermark_opacity, 1.0)),
        watermark_scale=max(0.3, min(watermark_scale, 3.0)),
        block_code_bg_color=block_code_bg_color,
        block_code_text_color=block_code_text_color,
        inline_code_bg_color=inline_code_bg_color,
        inline_code_text_color=inline_code_text_color,
        header_text=_css_string(header_text) if header_text else None,
        footer_text=_css_string(footer_text) if footer_text else None,
        page_numbers_enabled=page_numbers_enabled,
    )

    return HTML(string=full_html, base_url=base_dir).write_pdf()
