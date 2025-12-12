FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY . .

# Make entrypoint executable in image
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

# Copy application code
COPY . .

# Run the bot
CMD ["python", "main.py"]

