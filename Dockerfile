# Use the mirror-leech base image provided by the project author
FROM anasty17/mltb:latest

WORKDIR /usr/src/app

# ensure directory permissions (the original file had this)
RUN chmod 777 /usr/src/app || true

# create and use venv (same approach as original)
RUN python3 -m venv mltbenv

# copy only requirements first to use layer caching
COPY requirements.txt /usr/src/app/requirements.txt

# install required packages into venv
RUN mltbenv/bin/pip install --no-cache-dir -r /usr/src/app/requirements.txt

# copy the rest of the project
COPY . /usr/src/app

# make sure start.sh is executable (if needed)
RUN chmod +x /usr/src/app/start.sh || true

# start the app using the included start script (which activates venv)
CMD ["bash", "start.sh"]
