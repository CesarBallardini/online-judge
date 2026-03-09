FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libwebp-dev \
    zlib1g-dev \
    default-libmysqlclient-dev \
    pkg-config \
    git \
    curl \
    netcat-openbsd \
    gettext \
    rustc \
    cargo \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js 20 LTS for asset compilation
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get update && \
    apt-get install -y nodejs && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /site

# Clone DMOJ source code and initialize submodules
RUN git clone https://github.com/DMOJ/site.git /tmp/dmoj-site && \
    cd /tmp/dmoj-site && \
    git submodule init && \
    git submodule update && \
    cd / && \
    mv /tmp/dmoj-site/* /site/ && \
    mv /tmp/dmoj-site/.[^.]* /site/ 2>/dev/null || true && \
    rm -rf /tmp/dmoj-site

# Copy requirements and install Python dependencies
COPY requirements.txt /site/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy only our custom files (do NOT use COPY . . — it overwrites cloned source)
COPY dmoj/docker_settings.py /site/dmoj/
COPY dmoj_urls.py /site/

# Copy custom Django app (API views + management commands)
COPY custom_commands/ /site/custom_commands/

# Install Node.js dependencies for asset compilation
RUN npm install -g sass postcss-cli postcss autoprefixer

# Compile SASS stylesheets
RUN ./make_style.sh || echo "Warning: make_style.sh failed, continuing..."

# Compile i18n messages
RUN (python manage.py compilemessages || echo "Warning: compilemessages failed, continuing...") && \
    (python manage.py compilejsi18n || echo "Warning: compilejsi18n failed, continuing...")

# Create necessary directories
RUN mkdir -p /site/media /site/static /site/log /site/problems

# Dry-run collectstatic to verify setup
RUN python manage.py collectstatic --noinput --dry-run || true

# Create startup script
RUN cat <<'ENTRYPOINT_EOF' > /site/entrypoint.sh
#!/bin/bash
set -e

echo "Waiting for database..."
while ! nc -z $MYSQL_HOST $MYSQL_PORT; do
  sleep 0.1
done
echo "Database is up!"

if [ "$RUN_MIGRATIONS" = "true" ]; then
  echo "Running migrations and setup..."
  python manage.py migrate --noinput
  echo "Loading initial fixtures..."
  python manage.py loaddata navbar || echo "Navbar fixture already loaded or not found"
  python manage.py loaddata language_small || echo "Language fixture already loaded or not found"
  python manage.py seed_extra_languages
  python manage.py seed_judge
  python manage.py loaddata demo || echo "Demo fixture already loaded or not found"
  python manage.py collectstatic --noinput
else
  echo "Skipping migrations (RUN_MIGRATIONS not set to true)"
fi

exec "$@"
ENTRYPOINT_EOF
RUN chmod +x /site/entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/site/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "--insecure", "0.0.0.0:8080"]
