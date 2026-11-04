# SmartCloset API

Backend for personal wardrobe digitization and management built with Python and Django REST Framework.

The platform eliminates the primary friction point of digital wardrobe apps: manually photographing and cropping individual garments. It automates clothing ingestion through a two-step headless browser pipeline (URL preview -> user selection) and AI-assisted segmentation to generate clean, transparent catalog cutouts ready for outfit generation and cataloging.

## Project Status

The backend is currently in active development.

Implemented features:
- **Authentication & Security**: Stateless JWT authentication (`djangorestframework-simplejwt`) with Bearer token validation, automatic token rotation on refresh, and user registration endpoint.
- **Modular RESTful Architecture**: Independent domain apps (`wardrobe` and `outfits`) with dedicated routers and serializers.
- **Strict Data Isolation**: Multi-tenant user segmentation via `request.user` across all querysets, serializer validations, and permissions.
- **Advanced Query Filtering**: Declarative query parameters (`django-filter`) across seasons, occasions, and favorite flags.
- **Two-Step Store Ingestion Flow**:
  1. Headless browser preview extraction (`Playwright`) supporting dynamic client-side rendering (SPA), anti-bot evasion (Akamai/CDN), progressive lazy-loading scroll, and high-resolution media deduplication.
  2. Targeted multi-angle garment import (front view and optional back view).
- **Computer Vision Pipeline**: Resolution optimization with `Pillow` (LANCZOS downsampling), automated background removal using `rembg` (`u2netp` portable model with persistent CPU-optimized session), and tight bounding-box autocropping.
- **Dual Perspective Support**: Handles both front and back views per garment with automated transparency processing.
- **Quad-Image Storage Handling**: Preserves original source files and transparent PNG assets for both perspectives.
- **Outfit Composition & Management**:
  - `Outfit` model supporting Many-to-Many relationships to user-owned `ClothingItem` instances.
  - Granular ownership verification preventing cross-user item contamination.
  - Custom actions like `toggle-favorite` directly on outfits.
  - Read/write serializer decoupling (`clothes_ids` for ingestion, nested `ClothingItemSerializer` for retrieval).
  - Database query optimization using `prefetch_related('clothes')` to eliminate N+1 overhead.
  - Categorization by season (`Season.choices`) and occasion (`Occasion.choices`) with localized display mappings.

Next steps:
- Celery and Redis integration to process image segmentation asynchronously in background workers.
- Expand universal store scraping compatibility across non-Inditex retailers (Mango, Nike, ASOS).
- Digital canvas generator for multi-item outfit composition.
- LLM styling assistant contextualized with local weather forecasts and personal schedule.

## Tech Stack

- **Language**: Python 3.12+ (tested through 3.14)
- **Framework**: Django 6+
- **API & Auth**: Django REST Framework, djangorestframework-simplejwt
- **Filtering**: django-filter
- **Browser Automation & Scraping**: Playwright, requests
- **Computer Vision & AI**: rembg (`u2netp`), onnxruntime, Pillow
- **Database**: SQLite (local development, targeting PostgreSQL for production)

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

The API will be available at http://127.0.0.1:8000/ and the admin panel at http://127.0.0.1:8000/admin/.

## Key Endpoints

### Authentication (/api/auth/)

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/auth/register/ | Register a new user and receive initial access/refresh JWT tokens |
| POST | /api/auth/login/ | Authenticate with credentials and obtain access/refresh token pair |
| POST | /api/auth/refresh/ | Rotate refresh token and obtain a fresh access token |

### Wardrobe (/api/clothes/)

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/clothes/ | List authenticated user's clothing items (supports filtering by season, category, etc.) |
| POST | /api/clothes/ | Upload a clothing item manually (multipart/form-data) |
| POST | /api/clothes/extract-preview/ | Extract product images and title hint from a store URL via Playwright |
| POST | /api/clothes/import-url/ | Import selected garment images (front/back), run background removal, and save item |
| GET / PUT / PATCH / DELETE | /api/clothes/<id>/ | Retrieve, update, partially update, or delete a clothing item |

### Outfits (/api/outfits/)

| Method | Endpoint | Description |
|---|---|---|
| GET | /api/outfits/ | List authenticated user's outfits (with preloaded garment details, supports filters) |
| POST | /api/outfits/ | Create a new outfit linking existing ClothingItem IDs (clothes_ids) |
| GET / PUT / PATCH / DELETE | /api/outfits/<id>/ | Retrieve, update, partially update, or delete an outfit |
| POST | /api/outfits/<id>/toggle-favorite/ | Toggle favorite boolean state for the specified outfit |