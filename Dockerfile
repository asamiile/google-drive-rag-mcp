FROM python:3.11-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY main.py ./

# Required environment variables at runtime:
#   GOOGLE_APPLICATION_CREDENTIALS  - path to service account JSON inside the container
#   TARGET_FOLDER_IDS               - comma-separated Google Drive folder IDs

CMD ["uv", "run", "python", "main.py"]
