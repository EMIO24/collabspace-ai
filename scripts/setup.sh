#!/bin/bash

echo "Setting up CollabSpace AI..."

cd backend

echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Creating superuser..."
python manage.py createsuperuser --noinput || echo "Superuser already exists"

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Setup complete!"
echo "Start the server with: python manage.py runserver"
