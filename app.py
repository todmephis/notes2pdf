import io
import shutil

from flask import Flask, render_template, request, send_file

from utils.notion_import import NotionImportError, load_notion_export
from utils.pdf_export import available_themes, build_pdf

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB


@app.route("/")
def index():
    return render_template("index.html", themes=available_themes(), error=None)


@app.route("/convert", methods=["POST"])
def convert():
    file = request.files.get("file")
    if not file or not file.filename:
        return render_template("index.html", themes=available_themes(), error="Debes subir un archivo .md o .zip"), 400

    theme = request.form.get("theme", "minimal")
    accent_color = request.form.get("accent_color", "#2563eb")
    page_size = request.form.get("page_size", "A4")

    work_dir = None
    try:
        markdown_text, base_dir, title, work_dir = load_notion_export(file)
        pdf_bytes = build_pdf(
            markdown_text=markdown_text,
            base_dir=base_dir,
            title=title,
            theme=theme,
            accent_color=accent_color,
            page_size=page_size,
        )
    except NotionImportError as e:
        return render_template("index.html", themes=available_themes(), error=str(e)), 400
    finally:
        if work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{title}.pdf",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5050)
