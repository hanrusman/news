FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=news_aggregator.settings

# Set work directory
WORKDIR /app

# Install dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Command to run (using dev server for simplicity in personal setup, or use gunicorn)
# Using runserver 0.0.0.0:8000 allows us to see logs easily and reload if mounted
CMD python manage.py collectstatic --noinput && gunicorn --bind 0.0.0.0:8000 news_aggregator.wsgi:application
