FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml ./
COPY checker/ ./checker/

RUN pip install --no-cache-dir -e ".[dev]"

CMD ["python", "-m", "checker.main"]
