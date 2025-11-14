# CollabSpace AI

A full-stack, AI-powered team collaboration platform built with Django REST Framework and React.

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+

### Backend Setup

cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements/base.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver

### Using Docker

docker-compose up --build

## Project Structure

collabspace-ai/
├── backend/
├── frontend/
├── nginx/
├── docs/
└── scripts/

## Running Tests

cd backend
pytest

## License

MIT License
