import base64
import io
import os
import shutil

from flask import Flask, Response, render_template, request, send_file

from utils.i18n import translate_error
from utils.notion_import import NotionImportError, load_notion_export
from utils.pdf_export import available_themes, build_pdf

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024  # 25 MB


def _watermark_kwargs_from_request() -> dict:
    watermark_type = request.form.get("watermark_type", "none")

    if watermark_type == "image":
        image = request.files.get("watermark_image")
        if image and image.filename:
            data_uri = "data:{};base64,{}".format(
                image.mimetype or "image/png",
                base64.b64encode(image.read()).decode("ascii"),
            )
            return {"watermark_text": None, "watermark_image_data_uri": data_uri}
        return {"watermark_text": None, "watermark_image_data_uri": None}

    if watermark_type == "text":
        text = request.form.get("watermark_text", "").strip()
        return {"watermark_text": text or None, "watermark_image_data_uri": None}

    return {"watermark_text": None, "watermark_image_data_uri": None}


def _generate_pdf_from_request():
    """Procesa el archivo subido + opciones del formulario y devuelve (pdf_bytes, title)."""
    file = request.files.get("file")
    if not file or not file.filename:
        raise NotionImportError("no_file")

    watermark_kwargs = _watermark_kwargs_from_request()
    watermark_opacity = float(request.form.get("watermark_opacity", 0.15) or 0.15)
    watermark_scale = float(request.form.get("watermark_size", 100) or 100) / 100.0

    code_colors_enabled = "code_colors_enabled" in request.form
    code_colors_same = "code_colors_same" in request.form

    block_code_bg_color = block_code_text_color = None
    inline_code_bg_color = inline_code_text_color = None

    if code_colors_enabled:
        if code_colors_same:
            block_code_bg_color = inline_code_bg_color = request.form.get("code_bg_color")
            block_code_text_color = inline_code_text_color = request.form.get("code_text_color")
        else:
            block_code_bg_color = request.form.get("block_code_bg_color")
            block_code_text_color = request.form.get("block_code_text_color")
            inline_code_bg_color = request.form.get("inline_code_bg_color")
            inline_code_text_color = request.form.get("inline_code_text_color")

    header_text = request.form.get("header_text", "").strip() or None
    footer_text = request.form.get("footer_text", "").strip() or None
    page_numbers_enabled = "page_numbers_enabled" in request.form

    platform = request.form.get("platform", "notion")

    work_dir = None
    try:
        markdown_text, base_dir, title, work_dir = load_notion_export(file, platform=platform)
        pdf_bytes = build_pdf(
            markdown_text=markdown_text,
            base_dir=base_dir,
            title=title,
            theme=request.form.get("theme", "minimal"),
            accent_color=request.form.get("accent_color", "#2563eb"),
            page_size=request.form.get("page_size", "A4"),
            watermark_opacity=watermark_opacity,
            watermark_scale=watermark_scale,
            block_code_bg_color=block_code_bg_color,
            block_code_text_color=block_code_text_color,
            inline_code_bg_color=inline_code_bg_color,
            inline_code_text_color=inline_code_text_color,
            header_text=header_text,
            footer_text=footer_text,
            page_numbers_enabled=page_numbers_enabled,
            **watermark_kwargs,
        )
    finally:
        if work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)

    return pdf_bytes, title


@app.route("/health")
def health():
    return "ok"


@app.route("/")
def index():
    return render_template("index.html", themes=available_themes(), error=None)


@app.route("/convert", methods=["POST"])
def convert():
    try:
        pdf_bytes, title = _generate_pdf_from_request()
    except NotionImportError as e:
        lang = request.form.get("lang", "en")
        error = translate_error(e.code, lang, **e.params)
        return render_template("index.html", themes=available_themes(), error=error), 400

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{title}.pdf",
    )


@app.route("/preview", methods=["POST"])
def preview():
    """Genera el mismo PDF pero para mostrarlo inline en el iframe de vista previa."""
    try:
        pdf_bytes, _title = _generate_pdf_from_request()
    except NotionImportError as e:
        lang = request.form.get("lang", "en")
        error = translate_error(e.code, lang, **e.params)
        return Response(error, status=400, mimetype="text/plain")

    return Response(pdf_bytes, mimetype="application/pdf")


if __name__ == "__main__":
    app.run(debug=True, port=int(os.environ.get("PORT", 5050)))
