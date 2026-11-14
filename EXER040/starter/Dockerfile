# EXER040 — the Nimbus Helpdesk as a container image (starter).
#
# Build from the REPOSITORY ROOT, so the image can see pyproject.toml, aicourse/ and data/:
#     docker build -f EXER040/starter/Dockerfile -t nimbus-helpdesk .
# Run, with the configuration injected from your .env (the file itself is never in the image):
#     docker run --rm -p 8000:8000 --env-file .env nimbus-helpdesk

# Complete the six steps. Each TODO says what the line must achieve; check.py reads this file.

# 1. A small base image that already has Python 3.12 and uv.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# 2. Dependencies first, in their own layer: it is rebuilt only when the lockfile changes.
COPY pyproject.toml uv.lock README.md ./
COPY aicourse ./aicourse
# TODO: install exactly the locked versions, without development extras:  uv sync --frozen --no-dev

# 3. The application: only what the service needs. Never `COPY . .`, and never the .env file.
COPY data ./data
COPY EXER037/solution ./EXER037/solution
COPY EXER037/servers ./EXER037/servers
COPY EXER040/starter/service.py ./EXER040/starter/service.py

# 4. TODO: do not run as root. Create a user, give it /app (it writes the vector index there), switch to it:
#          RUN useradd --create-home --uid 10001 app && chown -R app:app /app
#          USER app

# 5. TODO: tell the platform the port (ENV PORT=8000, EXPOSE 8000) and add a HEALTHCHECK that requests
#          /healthz. There is no curl in a slim image; Python can do it:
#          CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"]

# 6. TODO: start the service in exec form (a JSON list), so it receives the stop signal directly:
#          CMD ["python", "EXER040/starter/service.py"]
