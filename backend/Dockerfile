FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Python dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Default SQLite path can be overridden via env DATABASE_URL
ENV DATABASE_URL="sqlite:////data/scaleup_nvidia.db" \
    ALLOWED_ORIGINS="http://localhost:3000"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


