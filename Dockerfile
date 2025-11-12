# Use a simple Python base or the project's preferred base
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libffi-dev build-essential \
 && pip install --no-cache-dir -r /app/requirements.txt \
 && rm -rf /var/lib/apt/lists/*

# Copy the application
COPY . /app

# Make start script executable if present
RUN chmod +x /app/start.sh || true

# Default start (Render will run this)
CMD ["bash", "start.sh"]
