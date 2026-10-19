# SmartCloset API

Backend for personal wardrobe digitization and management built with Python and Django REST Framework.

The platform eliminates the primary friction point of digital wardrobe apps: manually photographing and cropping individual garments. It automates clothing ingestion through direct store URL extraction and AI-assisted segmentation to generate clean, transparent catalog cutouts ready for outfit generation.

## Project Status

The backend is currently in active development.

Implemented features:
- Modular RESTful API architecture with complete CRUD endpoints for clothing items.
- User data isolation via `request.user` and permission controls across endpoints.
- URL import service with support for direct CDN media extraction (Inditex/Zara) and metadata scraping via OpenGraph, Twitter Cards, and JSON-LD (`BeautifulSoup4`).
- Computer vision pipeline: image resolution optimization with `Pillow` (LANCZOS downsampling), automated background removal using `rembg`, and tight bounding-box autocropping.
- Dual-image storage handling: preserves original source image and transparent PNG version.

Next steps:
- Celery and Redis integration to process image segmentation asynchronously in background workers.
- Digital canvas generator for multi-item outfit composition.
- Dual perspective support (front and back views per garment).
- LLM styling assistant contextualized with local weather forecasts and personal schedule.

## Tech Stack

- Language: Python 3.12+
- Framework: Django 6+
- API: Django REST Framework
- Filtering: django-filter
- Computer Vision: rembg, onnxruntime, Pillow
- Web Scraping: requests, beautifulsoup4
- Database: SQLite (local development, targeting PostgreSQL for production)

## Local Setup

1. Clone the repository and enter the directory:
   git clone https://github.com/TU_USUARIO/smartcloset-backend.git
   cd smartcloset-backend

2. Create and activate the virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate

3. Install dependencies:
   pip install -r requirements.txt

4. Run migrations and start the development server:
   python manage.py migrate
   python manage.py runserver

The API will be available at http://127.0.0.1:8000/api/clothes/ and the admin panel at http://127.0.0.1:8000/admin/.

## Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/clothes/ | List authenticated user's clothing items |
| POST | /api/clothes/ | Upload a clothing item manually |
| POST | /api/clothes/import-url/ | Import and process an item from an external URL |
| GET / PUT / DELETE | /api/clothes/<id>/ | Retrieve, update, or delete a clothing item |