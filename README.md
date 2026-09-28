# Notion → PDF

App en Flask para convertir reportes exportados de Notion (Markdown) a PDF, con temas y color de acento seleccionables.

## Uso

Notion exporta una página como `.md` suelto, o como `.zip` cuando incluye imágenes o subpáginas. Esta app acepta ambos formatos: si subes un `.zip`, se extrae de forma segura y las imágenes referenciadas en el markdown se resuelven automáticamente.

## Requisitos

- Python 3.11+
- Homebrew (macOS) con las librerías nativas de WeasyPrint:

```bash
brew install pango gdk-pixbuf libffi
```

## Instalación

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Ejecutar

```bash
python app.py
```

Abre http://127.0.0.1:5050

## Estructura

```
app.py                  # rutas Flask
templates/               # formulario web y plantilla base del PDF
static/themes/            # temas CSS disponibles (minimal, dark, academic)
utils/
  notion_import.py         # extracción segura de .md / .zip exportado de Notion
  md_render.py               # conversión Markdown -> HTML
  pdf_export.py                # generación del PDF con WeasyPrint
```
