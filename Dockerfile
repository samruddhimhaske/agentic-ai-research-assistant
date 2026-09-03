# ============================================================
# Dockerfile — Containerize the Backend
# ============================================================
# A Dockerfile is a recipe for building a Docker container.
# Docker lets you package your app + all its dependencies into
# a single portable "container" that runs the same everywhere.
#
# WHY USE DOCKER?
#   Without Docker: "It works on my machine" — different Python
#   versions, missing packages, OS differences cause problems.
#   With Docker: The container is identical everywhere.
#
# BUILD AND RUN:
#   docker build -t ai-research-agent .
#   docker run -p 8000:8000 --env-file .env ai-research-agent
#
# HOW TO READ THIS FILE:
#   Each line is an instruction that builds a layer of the image.
#   Layers are cached — if nothing changed, Docker reuses the cache.
# ============================================================

# --- BASE IMAGE ---
# Start from an official slim Python image.
# "slim" means it's a smaller image without unnecessary tools.
# This keeps our final image size small.
FROM python:3.11-slim

# --- SET WORKING DIRECTORY ---
# All subsequent commands run from /app inside the container.
# This is like "cd /app" but for the container.
WORKDIR /app

# --- ENVIRONMENT VARIABLES ---
# These prevent Python from writing .pyc files (not needed in containers)
# and ensure print() output appears immediately in logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# --- INSTALL SYSTEM DEPENDENCIES ---
# Some Python packages need system libraries to build.
# We install them here, then clean up to reduce image size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# --- COPY REQUIREMENTS FIRST (for Docker layer caching) ---
# We copy requirements.txt BEFORE the rest of the code.
# Why? Docker caches each layer. If we copy all code first,
# any code change would force a full pip install re-run.
# By copying requirements.txt first, pip install only re-runs
# when requirements.txt actually changes. Much faster!
COPY backend/requirements.txt .

# --- INSTALL PYTHON DEPENDENCIES ---
# --no-cache-dir: Don't cache pip downloads (saves space in container)
# --upgrade pip: Ensure pip is up to date first
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- COPY APPLICATION CODE ---
# Now copy the actual application code.
# Done after pip install so code changes don't invalidate the
# pip install cache layer.
COPY backend/ .

# --- EXPOSE PORT ---
# Tell Docker that this container listens on port 8000.
# This is documentation — you still need to map the port when running.
EXPOSE 8000

# --- HEALTH CHECK ---
# Docker will periodically run this to check the container is healthy.
# If /health returns anything other than 200, the container is "unhealthy".
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# --- RUN THE APPLICATION ---
# This is the command that starts our FastAPI server.
# $PORT is an environment variable — Render/Railway set it automatically.
# We fall back to 8000 if $PORT isn't set.
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}
