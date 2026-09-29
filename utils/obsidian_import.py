"""Preprocesamiento de markdown estilo Obsidian: wikilinks, embeds y frontmatter."""
import os
import re
import urllib.parse

FRONTMATTER_RE = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.DOTALL)
WIKILINK_EMBED_RE = re.compile(r"!\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")
WIKILINK_RE = re.compile(r"\[\[([^\]|]+?)(?:\|([^\]]+))?\]\]")
IMAGE_MD_RE = re.compile(r"(!\[[^\]]*\]\()([^)\s]+)(\))")


def strip_frontmatter(markdown_text: str) -> str:
    """Elimina el bloque YAML `--- ... ---` que Obsidian coloca al inicio de la nota."""
    return FRONTMATTER_RE.sub("", markdown_text, count=1)


def convert_wikilinks(markdown_text: str) -> str:
    """Convierte la sintaxis propia de Obsidian a markdown estándar.

    `![[imagen.png]]` / `![[imagen.png|300]]` -> imagen markdown normal.
    `[[Nota]]` / `[[Nota|Alias]]` -> texto plano (no hay navegación entre
    páginas dentro de un único PDF exportado).
    """
    def embed_repl(match: re.Match) -> str:
        target = match.group(1).strip()
        return f"![{os.path.basename(target)}]({target})"

    text = WIKILINK_EMBED_RE.sub(embed_repl, markdown_text)

    def link_repl(match: re.Match) -> str:
        target, alias = match.group(1).strip(), match.group(2)
        return (alias or target).strip()

    return WIKILINK_RE.sub(link_repl, text)


def resolve_asset_paths(markdown_text: str, md_dir: str, search_root: str) -> str:
    """Reescribe rutas de imagen que no existen junto a la nota buscándolas en
    todo el vault extraído. Obsidian suele centralizar los adjuntos en una
    carpeta compartida (ej. `attachments/`) en vez de junto a cada nota.
    """
    def repl(match: re.Match) -> str:
        prefix, path, suffix = match.group(1), match.group(2), match.group(3)
        if path.startswith(("http://", "https://", "data:")):
            return match.group(0)

        decoded = urllib.parse.unquote(path)
        if os.path.isfile(os.path.join(md_dir, decoded)):
            return match.group(0)

        basename = os.path.basename(decoded)
        for root, _dirs, files in os.walk(search_root):
            if basename in files:
                found = os.path.join(root, basename)
                rel = os.path.relpath(found, md_dir)
                return f"{prefix}{rel}{suffix}"

        return match.group(0)

    return IMAGE_MD_RE.sub(repl, markdown_text)


def preprocess(markdown_text: str, md_dir: str, search_root: str) -> str:
    text = strip_frontmatter(markdown_text)
    text = convert_wikilinks(text)
    return resolve_asset_paths(text, md_dir, search_root)
