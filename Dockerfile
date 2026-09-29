FROM python:3.12-slim

WORKDIR /app

# build-essential + libffi-dev: WeasyPrint's native deps (cffi, Pillow) don't
# always ship prebuilt wheels for armv7 — this lets pip compile them if needed.
# The rest (libpango/libgdk-pixbuf/shared-mime-info/fonts) are what WeasyPrint
# itself needs at runtime to render PDFs.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    zlib1g-dev \
    libjpeg62-turbo-dev \
    libopenjp2-7-dev \
    libtiff-dev \
    libfreetype-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu-core \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY utils ./utils
COPY templates ./templates
COPY static ./static

ENV PORT=5050
EXPOSE 5050

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD sh -c "curl -fsS http://127.0.0.1:${PORT}/health || exit 1"

CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --workers 2 --timeout 60 app:app"]
