"""Mensajes de error del backend, localizables por código."""

ERROR_MESSAGES = {
    "en": {
        "no_file": "You must upload a .md or .zip file",
        "invalid_extension": "Only .md or .zip files are accepted",
        "unsafe_zip_entry": "Unsafe zip entry: {name}",
        "no_markdown_in_zip": "No .md file was found inside the zip.",
    },
    "es": {
        "no_file": "Debes subir un archivo .md o .zip",
        "invalid_extension": "Solo se aceptan archivos .md o .zip",
        "unsafe_zip_entry": "Entrada de zip insegura: {name}",
        "no_markdown_in_zip": "No se encontró ningún archivo .md dentro del zip.",
    },
}


def translate_error(code: str, lang: str, **params) -> str:
    messages = ERROR_MESSAGES.get(lang, ERROR_MESSAGES["en"])
    template = messages.get(code, code)
    return template.format(**params)
