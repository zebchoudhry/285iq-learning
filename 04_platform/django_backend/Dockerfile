# 285IQ Learning Platform - Production image
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Static root for collectstatic (no DB required)
RUN mkdir -p staticfiles

EXPOSE 8000

# Run with gunicorn; use 0.0.0.0 so container accepts external connections
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "studymate285.wsgi:application"]
