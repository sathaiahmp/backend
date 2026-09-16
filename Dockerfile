FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (separate layer — cached unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run FastAPI with Uvicorn.
# - Listens on 0.0.0.0 (required for Docker networking)
# - Uses Render's PORT environment variable in production (default 10000)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
