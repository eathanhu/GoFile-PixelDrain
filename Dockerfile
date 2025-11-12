FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Install ntpdate for quick time sync and ca-certificates for HTTPS
RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata ntpdate ca-certificates \
 && pip install --no-cache-dir -r /app/requirements.txt \
 && rm -rf /var/lib/apt/lists/*

COPY . /app

# Ensure start.sh is executable
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
