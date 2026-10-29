# SmartCloset API

Backend for personal wardrobe digitization and management built with Python and Django REST Framework.

The platform eliminates the primary friction point of digital wardrobe apps: manually photographing and cropping individual garments. It automates clothing ingestion through a two-step headless browser pipeline (URL preview -> user selection) and AI-assisted segmentation to generate clean, transparent catalog cutouts ready for outfit generation.

## Project Status

The backend is currently in active development.

Implemented features:
- Modular RESTful API architecture with complete CRUD endpoints for clothing items.
- User data isolation via `request.user` and permission controls across endpoints.
- Two-step store ingestion flow:
  1. Headless browser preview extraction (`Playwright`) supporting dynamic client-side rendering (SPA), anti-bot evasion (Akamai/CDN), progressive lazy-loading scroll, and high-resolution media deduplication.
  2. Targeted multi-angle garment import (front view and optional back view).
- Computer vision pipeline: resolution optimization with `Pillow` (LANCZOS downsampling), automated background removal using `rembg` (`u2netp` portable model with persistent CPU-optimized session), and tight bounding-box autocropping.
- Dual perspective support: handles both front and back views per garment with automated transparency processing.
- Quad-image storage handling: preserves original source files and transparent PNG assets for both perspectives.

Next steps:
- Celery and Redis integration to process image segmentation asynchronously in background workers.
- Expand universal store scraping compatibility across non-Inditex retailers (Mango, Nike, ASOS).
- Digital canvas generator for multi-item outfit composition.
- LLM styling assistant contextualized with local weather forecasts and personal schedule.

## Tech Stack

- Language: Python 3.12+
- Framework: Django 6+
- API: Django REST Framework
- Filtering: django-filter
- Browser Automation & Scraping: Playwright, requests, beautifulsoup4
- Computer Vision & AI: rembg (`u2netp`), onnxruntime, Pillow
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
playwright install chromium

4. Run migrations and start the development server:
python manage.py migrate
python manage.py runserver

The API will be available at http://127.0.0.1:8000/api/clothes/ and the admin panel at http://127.0.0.1:8000/admin/.

## Key Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/clothes/ | List authenticated user's clothing items |
| POST | /api/clothes/ | Upload a clothing item manually (multipart/form-data) |
| POST | /api/clothes/extract-preview/ | Extract product images and title hint from a store URL via Playwright |
| POST | /api/clothes/import-url/ | Import selected garment images (front/back), run background removal, and save item |
| GET / PUT / DELETE | /api/clothes/<id>/ | Retrieve, update, or delete a clothing item |