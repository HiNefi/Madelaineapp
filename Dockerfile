# ── Build stage ──────────────────────────────────────────────────────────────
FROM python:3.11-slim

# Install Chromium + chromedriver (same version, no download needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── App ───────────────────────────────────────────────────────────────────────
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persist WhatsApp session via Railway Volume mounted at /data
ENV WA_SESSION_DIR=/data/whatsapp_session
ENV DB_PATH=/data/love_messages.db
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV PYTHONUNBUFFERED=1

EXPOSE 5000

# Use gunicorn in production; one worker keeps the singleton driver alive
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1",\
     "--timeout", "120", "--access-logfile", "-", "app:app"]
