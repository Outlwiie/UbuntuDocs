# ── Base image ─────────────────────────────────────────────────────────────────
# We use a slim Python image to keep the container small
FROM python:3.11-slim

# ── Working directory ───────────────────────────────────────────────────────────
WORKDIR /app

# ── Install dependencies ────────────────────────────────────────────────────────
# Copy requirements first — Docker caches this layer so it only
# reinstalls packages when requirements.txt actually changes
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ── Copy source code ────────────────────────────────────────────────────────────
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# ── Expose port ─────────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Start the server ────────────────────────────────────────────────────────────
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]