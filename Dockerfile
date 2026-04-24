FROM python:3.12-slim

WORKDIR /app

RUN pip install uv --no-cache-dir

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uv", "run", "granian", "--interface", "asgi", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
