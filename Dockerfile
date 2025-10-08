FROM python:3.10.12-alpine

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    postgresql-dev \
    gcc \
    musl-dev \
    libffi-dev

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Create a non-root user
RUN adduser -D -s /bin/sh appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "python manage.py migrate && python manage.py setup_admin && gunicorn InventoryMS.wsgi:application --bind 0.0.0.0:8000 --workers 3 --timeout 120"]
