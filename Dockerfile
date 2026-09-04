FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better Docker caching
COPY backend/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy backend
COPY backend/ /app/backend/

# Copy frontend
COPY frontend/ /app/frontend/

# Backend working directory
WORKDIR /app/backend

# Start FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "10000"]
