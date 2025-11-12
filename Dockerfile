FROM python:3.11-slim

# Install extras for time sync
RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata ntpdate && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

# sync time once at container start, then run
ENTRYPOINT ["/bin/bash", "-lc", "ntpdate -u pool.ntp.org || true; exec python main.py"]
