# EXER041 — the Nimbus Helpdesk as a container image (reference solution).
#
# Build from the REPOSITORY ROOT, so the image can see pyproject.toml, aicourse/ and data/:
#     docker build -f EXER041/solution/Dockerfile -t nimbus-helpdesk .
# Run, with the configuration injected from your .env (the file itself is never in the image):
#     docker run --rm -p 8000:8000 --env-file .env nimbus-helpdesk

# 1. A small base image that already has Python 3.12 and uv.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# 2. Dependencies first, in their own layer: it is rebuilt only when the lockfile changes.
#    --frozen installs exactly what uv.lock says, the same versions you tested with.
COPY pyproject.toml uv.lock README.md ./
COPY aicourse ./aicourse
RUN uv sync --frozen --no-dev

# 3. The application: only what the service needs. No .env, no tests, no other exercises.
COPY data ./data
COPY EXER037/solution ./EXER037/solution
COPY EXER037/servers ./EXER037/servers
COPY EXER041/solution/service.py ./EXER041/solution/service.py

# 4. Do not run as root. The app user owns /app, so it can write its vector index and notes.
RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

# 5. What the platform needs to know: the port, and how to ask "are you alive?".
ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/healthz', timeout=3)"]

# 6. Exec form (a JSON list): the service is process 1 and receives the stop signal directly.
CMD ["python", "EXER041/solution/service.py"]
