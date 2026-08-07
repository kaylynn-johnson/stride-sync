# Pull base image
FROM python:3.14-slim-bookworm

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /usr/src/app

# Copy requirements txt
COPY requirements.txt /usr/src/app/

# Install dependencies
RUN pip3 install -r requirements.txt

# Copy project
COPY . /usr/src/app/

# Collect static assets at build time (whitenoise serves these directly, no
# separate nginx/CDN needed). Doesn't require DB access or a real SECRET_KEY.
RUN python3 manage.py collectstatic --noinput

# Run as a non-root user
RUN useradd -m appuser && chown -R appuser /usr/src/app
USER appuser

EXPOSE 8000

# Production default; docker-compose.yml overrides this with `runserver` for
# local dev. WEB_CONCURRENCY sets the gunicorn worker count (default 3).
CMD ["sh", "-c", "gunicorn stride_sync.wsgi:application --bind 0.0.0.0:8000 --workers ${WEB_CONCURRENCY:-3}"]
