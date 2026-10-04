# syntax=docker/dockerfile:1.7

ARG PYTHON_VERSION=3.12
ARG UV_VERSION=0.12.22

FROM ghcr.io/astral-sh/uv:${UV_VERSION} AS uv

FROM python:${PYTHON_VERSION}-slim-bookworm AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=0 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        ffmpeg \
        git \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /bin/

WORKDIR /workspace

# Dependency layer. If the repository already contains uv.lock, enforce it.
# On the very first build uv resolves pyproject.toml and creates a lock inside
# the image; the dev startup script creates the host-side lock in the bind mount.
FROM base AS dev
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.,target=/context,ro \
    cp /context/pyproject.toml /workspace/pyproject.toml \
    && if [ -f /context/uv.lock ]; then \
         cp /context/uv.lock /workspace/uv.lock \
         && uv sync --locked --no-install-project --group dev; \
       else \
         uv sync --no-install-project --group dev; \
       fi
CMD ["sleep", "infinity"]

# Runtime image for later non-development execution.
FROM base AS runtime
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=.,target=/context,ro \
    cp /context/pyproject.toml /workspace/pyproject.toml \
    && if [ -f /context/uv.lock ]; then \
         cp /context/uv.lock /workspace/uv.lock \
         && uv sync --locked --no-install-project --no-dev; \
       else \
         uv sync --no-install-project --no-dev; \
       fi
COPY src ./src
COPY README.md ./README.md
RUN --mount=type=cache,target=/root/.cache/uv \
    if [ -f uv.lock ]; then uv sync --locked --no-dev; else uv sync --no-dev; fi
CMD ["python", "-m", "ball_cv", "doctor"]
