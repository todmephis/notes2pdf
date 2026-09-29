"""Extrae contenido exportado desde Notion/Obsidian (.md suelto o .zip con assets)."""
import os
import re
import tempfile
import zipfile
from werkzeug.utils import secure_filename

from . import obsidian_import

ALLOWED_EXTENSIONS = {".md", ".zip"}


class NotionImportError(Exception):
    """Error localizable: `code` se traduce en utils/i18n.py, `params` rellena el mensaje."""

    def __init__(self, code: str, **params):
        self.code = code
        self.params = params
        super().__init__(code)


def _safe_extract(zip_path: str, dest_dir: str) -> None:
    """Extrae el zip evitando path traversal (zip slip)."""
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            target_path = os.path.realpath(os.path.join(dest_dir, member))
            if not target_path.startswith(os.path.realpath(dest_dir) + os.sep):
                raise NotionImportError("unsafe_zip_entry", name=member)
        zf.extractall(dest_dir)


def _find_main_markdown(root_dir: str) -> str:
    """Busca el .md principal dentro de la carpeta extraída.

    El export de Notion suele generar:
      Pagina.md
      Pagina/ (assets + subpaginas)
    Tomamos el .md de nivel más superficial y, si hay varios al mismo nivel,
    el de mayor tamaño (suele ser la página raíz, no una subpágina).
    """
    md_files = []
    for dirpath, _dirnames, filenames in os.walk(root_dir):
        depth = os.path.relpath(dirpath, root_dir).count(os.sep)
        for name in filenames:
            if name.lower().endswith(".md"):
                full_path = os.path.join(dirpath, name)
                md_files.append((depth, -os.path.getsize(full_path), full_path))

    if not md_files:
        raise NotionImportError("no_markdown_in_zip")

    md_files.sort()
    return md_files[0][2]


def load_notion_export(file_storage, platform: str = "notion") -> tuple[str, str, str, str]:
    """Procesa el archivo subido por el usuario.

    `platform` determina el preprocesamiento de markdown a aplicar:
    "notion" (por defecto) no aplica ninguno; "obsidian" convierte wikilinks
    y embeds a markdown estándar, limpia el frontmatter YAML, y busca los
    adjuntos en todo el vault si no están junto a la nota.

    Devuelve (markdown_text, base_dir, titulo, work_dir).
    base_dir es la carpeta desde la que WeasyPrint debe resolver imágenes
    relativas (se usa como base_url). work_dir es la carpeta temporal raíz
    que el llamador debe borrar por completo al terminar.
    """
    filename = secure_filename(file_storage.filename or "")
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise NotionImportError("invalid_extension")

    work_dir = tempfile.mkdtemp(prefix="notes2pdf_")
    extract_dir = work_dir

    if ext == ".zip":
        zip_path = os.path.join(work_dir, filename)
        file_storage.save(zip_path)
        extract_dir = os.path.join(work_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)
        _safe_extract(zip_path, extract_dir)
        md_path = _find_main_markdown(extract_dir)
    else:
        md_path = os.path.join(work_dir, filename)
        file_storage.save(md_path)

    with open(md_path, "r", encoding="utf-8") as f:
        markdown_text = f.read()

    base_dir = os.path.dirname(md_path)

    if platform == "obsidian":
        markdown_text = obsidian_import.preprocess(markdown_text, base_dir, extract_dir)

    title = _extract_title(markdown_text) or os.path.splitext(os.path.basename(md_path))[0]

    return markdown_text, base_dir, title, work_dir


def _extract_title(markdown_text: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", markdown_text, re.MULTILINE)
    return match.group(1).strip() if match else None
