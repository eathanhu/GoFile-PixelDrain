# Dockerfile — sync time then start bot
FROM python:3.11-slim

# keep output unbuffered for logs
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# copy and install python deps first (cache friendliness)
COPY requirements.txt /app/requirements.txt

# Install ntpdate for time sync, ca-certificates for HTTPS, then install python deps
RUN apt-get update \
 && apt-get install -y --no-install-recommends ntpdate ca-certificates \
 && pip install --no-cache-dir -r /app/requirements.txt \
 && rm -rf /var/lib/apt/lists/*

# copy project files
COPY . /app

# add start wrapper
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# run the wrapper (ntpdate then python main)
CMD ["/app/start.sh"]
