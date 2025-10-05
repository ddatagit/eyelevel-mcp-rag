FROM python:3.10.18-slim-trixie

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml .
COPY main.py .

RUN uv sync

EXPOSE 8000

CMD ["uv", "run", "main.py"]