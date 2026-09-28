"""Conversión de Markdown (estilo Notion) a HTML."""
import markdown

MD_EXTENSIONS = [
    "extra",          # tablas, footnotes, abbr, etc.
    "sane_lists",
    "codehilite",
    "toc",
    "nl2br",
]

MD_EXTENSION_CONFIGS = {
    "codehilite": {"guess_lang": False, "css_class": "highlight"},
}


def render_markdown_to_html(markdown_text: str) -> str:
    return markdown.markdown(
        markdown_text,
        extensions=MD_EXTENSIONS,
        extension_configs=MD_EXTENSION_CONFIGS,
    )
