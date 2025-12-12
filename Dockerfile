FROM python:3.11-slim

# Make Python output flush directly
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install ntpdate for time synchronization
RUN apt-get update && \
    apt-get install -y --no-install-recommends ntpdate ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements first to allow layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project

# Make entrypoint.sh executable
RUN chmod +x /app/entrypoint.sh

# Run your custom entrypoint (syncs time → starts bot)
ENTRYPOINT ["/app/entrypoint.sh"]


# Copy application code
COPY . .

# Run the bot
CMD ["python", "main.py"]

