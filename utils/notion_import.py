"""Extrae contenido exportado desde Notion (.md suelto o .zip con assets)."""
import os
import re
import tempfile
import zipfile
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {".md", ".zip"}


class NotionImportError(Exception):
    pass


def _safe_extract(zip_path: str, dest_dir: str) -> None:
    """Extrae el zip evitando path traversal (zip slip)."""
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            target_path = os.path.realpath(os.path.join(dest_dir, member))
            if not target_path.startswith(os.path.realpath(dest_dir) + os.sep):
                raise NotionImportError(f"Entrada de zip insegura: {member}")
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
        raise NotionImportError("No se encontró ningún archivo .md dentro del zip.")

    md_files.sort()
    return md_files[0][2]


def load_notion_export(file_storage) -> tuple[str, str, str, str]:
    """Procesa el archivo subido por el usuario.

    Devuelve (markdown_text, base_dir, titulo, work_dir).
    base_dir es la carpeta desde la que WeasyPrint debe resolver imágenes
    relativas (se usa como base_url). work_dir es la carpeta temporal raíz
    que el llamador debe borrar por completo al terminar.
    """
    filename = secure_filename(file_storage.filename or "")
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise NotionImportError("Solo se aceptan archivos .md o .zip")

    work_dir = tempfile.mkdtemp(prefix="notion2pdf_")

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
    title = _extract_title(markdown_text) or os.path.splitext(os.path.basename(md_path))[0]

    return markdown_text, base_dir, title, work_dir


def _extract_title(markdown_text: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", markdown_text, re.MULTILINE)
    return match.group(1).strip() if match else None
