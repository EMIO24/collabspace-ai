FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y \
    postgresql-client \
    netcat-traditional \
    && rm -rf /var/lib/apt/lists/*
COPY requirements/base.txt requirements/
RUN pip install --upgrade pip
RUN pip install -r requirements/base.txt
COPY . .
RUN mkdir -p logs media static
RUN python manage.py collectstatic --noinput || true
EXPOSE 8000
CMD ["gunicorn", "collabspace_backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
