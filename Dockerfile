# Stage 1: prepare Python dependencies
FROM python:3.14-slim AS builder

WORKDIR /build

RUN umask 022 && python -m venv /opt/venv

COPY requirements.txt .
RUN umask 022 && /opt/venv/bin/python -m pip install \
    --no-cache-dir -r requirements.txt


# Stage 2: run the application
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY --from=builder /opt/venv /opt/venv

COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

RUN find /app -type d -exec chmod 755 {} + \
    && find /app -type f -exec chmod 644 {} +

USER appuser

# Verify runtime dependencies are readable by the application user.
RUN python -c "import os; assert os.geteuid() == 10001; import flask, gunicorn.app.wsgiapp, psycopg"

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "1", "--worker-class", "gthread", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
