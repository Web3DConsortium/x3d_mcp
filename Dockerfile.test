FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
COPY src/ src/
COPY tests/ tests/
COPY dataset/ dataset/
COPY examples/ examples/

RUN pip install --no-cache-dir ".[dev]"

ENV PYTHONPATH=/app/src:/app

CMD ["python", "-m", "pytest", "tests/", "-v"]
