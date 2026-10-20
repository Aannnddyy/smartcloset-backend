import io
import re
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from django.core.files.base import ContentFile
from PIL import Image
from playwright.sync_api import sync_playwright
from rembg import new_session, remove

COMMON_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
}

# Sesión ligera con u2netp para evitar saturar la CPU del Mac
SESSION_REMBG = new_session(model_name="u2netp")


def remove_background_and_crop(image_field, max_size=(800, 800)) -> ContentFile:
    """
    Reduce tamaño de imagen, remueve fondo con sesión ligera u2netp
    y recorta los bordes transparentes sobrantes.
    """
    if hasattr(image_field, 'open'):
        image_field.open()

    image_field.seek(0)

    # 1. Reducción proporcional previa con Pillow
    img = Image.open(image_field)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    temp_buffer = io.BytesIO()
    img.save(temp_buffer, format="PNG")
    temp_buffer.seek(0)

    # 2. Eliminación de fondo reutilizando la sesión optimizada
    output_bytes = remove(temp_buffer.getvalue(), session=SESSION_REMBG)

    # 3. Recorte automático a los límites reales de la prenda
    processed_img = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
    bounding_box = processed_img.getbbox()
    if bounding_box:
        processed_img = processed_img.crop(bounding_box)

    # 4. Guardado final optimizado
    final_buffer = io.BytesIO()
    processed_img.save(final_buffer, format="PNG", optimize=True)
    final_buffer.seek(0)

    original_name = image_field.name.split('/')[-1].split('.')[0]
    filename = f"processed_{original_name}.png"
    return ContentFile(final_buffer.getvalue(), name=filename)


def download_image_from_url(image_url: str) -> ContentFile:
    """
    Descarga una imagen desde su URL directa y la devuelve como ContentFile de Django.
    """
    response = requests.get(image_url, headers=COMMON_HEADERS, timeout=15)
    response.raise_for_status()

    parsed_path = urlparse(image_url).path
    filename = parsed_path.split('/')[-1]

    if not filename or '.' not in filename:
        filename = "garment_item.jpg"
    elif '?' in filename:
        filename = filename.split('?')[0]

    return ContentFile(response.content, name=filename)


def clean_and_deduplicate_urls(raw_urls: list) -> list:
    """
    Agrupa imágenes por su identificador base, elimina resoluciones intermedias
    y descarta miniaturas pequeñas (w < 400).
    """
    unique_images = {}

    for url in raw_urls:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        # Si incluye parámetro de anchura (w=...), filtramos miniaturas
        if 'w' in params:
            try:
                width = int(params['w'][0])
                if width < 400:
                    continue
            except ValueError:
                pass

        # Obtenemos la ruta base sin query params para agrupar duplicados
        base_path = parsed.path

        # En Zara y otros CDNs, forzamos la versión en alta resolución (w=2048)
        if 'w' in params:
            params['w'] = ['2048']
            clean_query = urlencode(params, doseq=True)
            normalized_url = urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                clean_query,
                parsed.fragment
            ))
        else:
            normalized_url = url

        # Guardamos usando la ruta base como clave para no repetir la misma toma
        if base_path not in unique_images:
            unique_images[base_path] = normalized_url

    return list(unique_images.values())


def extract_product_preview(product_url: str) -> dict:
    title_hint = ""

    ignored_keywords = [
        'logo', 'icon', 'pixel', 'avatar', 'badge', 'banner',
        'rating', 'star', 'arrow', 'payment', 'footer', 'header',
        'cart', 'bag', 'heart', 'flag'
    ]

    valid_extensions = ['.jpg', '.jpeg', '.webp', '.png', '.avif']

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            channel="chrome",
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
            ]
        )

        context = browser.new_context(
            user_agent=COMMON_HEADERS['User-Agent'],
            locale="es-ES",
            viewport={"width": 1440, "height": 900}
        )

        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        try:
            page.goto(product_url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(2000)

            # Scroll progresivo para asegurar la carga completa de fotos traseras y de detalle
            page.evaluate("""
                async () => {
                    for (let i = 0; i < 5; i++) {
                        window.scrollBy(0, 1000);
                        await new Promise(r => setTimeout(r, 400));
                    }
                }
            """)
            page.wait_for_timeout(1000)

            title_hint = page.title()
            for sep in ['|', '-', '—', '•']:
                if sep in title_hint:
                    title_hint = title_hint.split(sep)[0].strip()
                    break

            raw_sources = page.evaluate("""
                () => {
                    const urls = [];
                    document.querySelectorAll('img, picture source, source').forEach(el => {
                        const src = el.getAttribute('src') 
                            || el.getAttribute('data-src') 
                            || el.getAttribute('data-original') 
                            || el.getAttribute('srcset')
                            || el.getAttribute('data-srcset');
                        if (src) urls.push(src);
                    });
                    return urls;
                }
            """)

            filtered_sources = []
            for raw in raw_sources:
                target = raw

                if ',' in target:
                    target = target.split(',')[-1].strip().split(' ')[0]
                elif ' ' in target:
                    target = target.strip().split(' ')[0]

                if target.startswith('//'):
                    target = f"https:{target}"

                target_lower = target.lower()
                has_format = any(ext in target_lower for ext in valid_extensions)
                is_cdn = any(term in target_lower for term in ['/image', '/foto', '/product', 'cdn', 'media', 'static'])
                is_ignored = any(kw in target_lower for kw in ignored_keywords)

                if (has_format or is_cdn) and not is_ignored and target.startswith('http'):
                    filtered_sources.append(target)

            candidates = clean_and_deduplicate_urls(filtered_sources)

        finally:
            browser.close()

    if not candidates:
        raise ValueError("No se encontraron imágenes en el producto facilitado.")

    return {
        "title_hint": title_hint,
        "images": candidates[:15]
    }