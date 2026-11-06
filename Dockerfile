FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src/ src/
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir . \
    && groupadd --system --gid 10001 shotlist \
    && useradd --system --uid 10001 --gid shotlist --no-create-home shotlist \
    && mkdir -p /export \
    && chown 10001:10001 /export

USER 10001:10001
ENTRYPOINT ["shotlist"]
CMD ["--help"]
