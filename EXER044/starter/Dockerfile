# EXER044 — the helpdesk with limits and graceful shutdown, as a container image (given).
#
# Build from the REPOSITORY ROOT:
#     docker build -f EXER044/starter/Dockerfile -t nimbus-helpdesk-load .
# Run, and stop it the way a platform does:
#     docker run -d --name helpdesk -p 8000:8000 --env-file .env nimbus-helpdesk-load
#     time docker stop helpdesk          # seconds, not the 10 s of EXER041: the service handles SIGTERM

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

COPY pyproject.toml uv.lock README.md ./
COPY aicourse ./aicourse
RUN uv sync --frozen --no-dev

# The lessons this service is built from, and nothing else.
COPY data ./data
COPY EXER037/solution ./EXER037/solution
COPY EXER037/servers ./EXER037/servers
COPY EXER041/solution/service.py ./EXER041/solution/service.py
COPY EXER042/solution/secure_service.py ./EXER042/solution/secure_service.py
COPY EXER044/starter/load_service.py ./EXER044/starter/load_service.py

RUN useradd --create-home --uid 10001 app && chown -R app:app /app
USER app

ENV PORT=8000 SHUTDOWN_GRACE_SECONDS=25
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8000') + '/healthz', timeout=3)"]

# SIGTERM is Docker's default stop signal; written out because the service depends on it.
# The grace period must be longer than SHUTDOWN_GRACE_SECONDS: docker stop -t 30, or the
# platform's termination grace period (Kubernetes: terminationGracePeriodSeconds, default 30).
STOPSIGNAL SIGTERM
CMD ["python", "EXER044/starter/load_service.py"]
